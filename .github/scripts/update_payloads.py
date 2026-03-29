#!/usr/bin/env python3
"""
Payload auto-update script for PS5 UMTX2 Jailbreak v2.
Reads .github/payloads.yaml and metadata.json files, downloads latest payload binaries,
and generates document/en/ps5/payload_map.js with the new v2 format.

Features:
- GitHub Releases API integration with changelog parsing
- License auto-detection
- Pre-release flag detection
- Firmware compatibility auto-detection (topics + README)
- metadata.json generation/maintenance
- payload_map.js v2 format with filePath support
"""

import os
import sys
import json
import hashlib
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
    import yaml

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PAYLOADS_DIR = REPO_ROOT / "document" / "en" / "ps5" / "payloads"
PAYLOAD_MAP_FILE = REPO_ROOT / "document" / "en" / "ps5" / "payload_map.js"
PAYLOAD_CONFIG_FILE = REPO_ROOT / ".github" / "payloads.yaml"

MAX_VERSIONS_PER_PAYLOAD = 999  # Effectively unlimited - fetch all available versions
CUSTOM_ACTION_APPCACHE_REMOVE = "appcache-remove"

# Version author patterns for license detection
AUTHOR_PATTERNS = {
    "MIT": ["john-tornblom"],
    "GPL": ["LightningMods", "sleirsgoevy", "EchoStretch"],
}


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_file(url: str, dest_path: Path) -> tuple[str, int]:
    """Download a file from URL and return (hash, size)."""
    print(f"  Downloading: {url}")
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    temp_path = dest_path.with_suffix('.tmp')
    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    file_hash = calculate_file_hash(temp_path)
    file_size = temp_path.stat().st_size
    temp_path.rename(dest_path)

    print(f"  Saved: {dest_path.name} ({file_size} bytes, hash: {file_hash[:16]}...)")
    return file_hash, file_size


def parse_changelog(release_body: str) -> List[str]:
    """Parse GitHub release body into changelog entries."""
    if not release_body:
        return []
    
    entries = []
    for line in release_body.strip().split('\n'):
        line = line.strip()
        # Skip empty lines and headers
        if not line or line.startswith('#'):
            continue
        # Remove markdown list markers
        if line.startswith(('- ', '* ', '+ ')):
            line = line[2:]
        elif re.match(r'^\d+\.\s', line):
            line = re.sub(r'^\d+\.\s', '', line)
        # Skip "Full Changelog" links
        if 'Full Changelog' in line or line.startswith('http'):
            continue
        if line:
            entries.append(line.strip())
    
    return entries[:10]  # Max 10 entries per version


def detect_license(repo: str, manual_license: Dict[str, str]) -> Dict[str, str]:
    """Detect license info from GitHub API."""
    # Priority 1: Manual override
    if manual_license.get('type'):
        return manual_license
    
    try:
        result = subprocess.run(
            ["gh", "repo", "view", repo, "--json", "licenseInfo"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            license_info = data.get('licenseInfo', {})
            spdx_id = license_info.get('spdxId', 'Unknown')
            if spdx_id == 'NOASSERTION':
                spdx_id = 'Unknown'
            return {
                "type": spdx_id,
                "url": f"https://github.com/{repo}/blob/main/LICENSE"
            }
    except Exception:
        pass
    
    return {"type": "Unknown", "url": ""}


def detect_firmware_compatibility(repo: str, manual_firmwares: List[str]) -> List[str]:
    """Detect supported firmwares from multiple sources."""
    # Priority 1: Manual override
    if manual_firmwares:
        return manual_firmwares
    
    # Priority 2: GitHub topics
    try:
        result = subprocess.run(
            ["gh", "repo", "view", repo, "--json", "repositoryTopics"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            topics = data.get('repositoryTopics', [])
            topic_names = [t.get('name', '') for t in topics]
            
            fw_from_topics = []
            for topic in topic_names:
                if 'ps5-fw' in topic or 'fw-' in topic:
                    # Extract version from topic like "ps5-fw-3xx" -> "3."
                    match = re.search(r'[45]\.?', topic)
                    if match:
                        fw_prefix = match.group(0)
                        if not fw_prefix.endswith('.'):
                            fw_prefix += '.'
                        if fw_prefix not in fw_from_topics:
                            fw_from_topics.append(fw_prefix)
            
            if fw_from_topics:
                return fw_from_topics
    except Exception:
        pass
    
    # Priority 3: README parse
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/readme", "--jq", ".content"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            import base64
            readme_content = base64.b64decode(result.stdout).decode('utf-8', errors='ignore')
            
            # Look for firmware mentions in README
            fw_patterns = [
                r'(?:firmware|fw|supports?).*?([345]\.[0-9]+)',
                r'([345]\.[0-9]+).*?(?:firmware|fw|supports?)',
            ]
            
            found_fw = set()
            for pattern in fw_patterns:
                matches = re.findall(pattern, readme_content, re.IGNORECASE)
                for match in matches:
                    major = match.split('.')[0]
                    prefix = f"{major}."
                    if prefix not in found_fw:
                        found_fw.add(prefix)
            
            if found_fw:
                return sorted(list(found_fw), reverse=True)
    except Exception:
        pass
    
    # Priority 4: No restriction
    return []


def get_github_releases(repo: str, max_releases: int = MAX_VERSIONS_PER_PAYLOAD) -> List[Dict]:
    """Get releases from a GitHub repo using gh CLI.
    
    Note: 'gh release list' does NOT support 'body' field.
    Only available fields: createdAt, isDraft, isImmutable, isLatest,
    isPrerelease, name, publishedAt, tagName.
    Use get_release_details() to fetch body/assets per release.
    """
    try:
        result = subprocess.run(
            ["gh", "release", "list", "--repo", repo, "--json",
             "tagName,name,isPrerelease", "--limit", str(max_releases)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  Warning: gh release list failed for {repo}: {result.stderr}")
            return []

        releases = json.loads(result.stdout)
        return releases
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not fetch releases for {repo}: {e}")
        return []


def get_release_details(repo: str, tag: str) -> Optional[Dict]:
    """Get release details (body, url, assets) for a specific tag using gh release view.
    
    This is the second step after get_github_releases(), since 'gh release list'
    does not support the 'body' field.
    """
    try:
        result = subprocess.run(
            ["gh", "release", "view", tag, "--repo", repo,
             "--json", "body,url,assets,createdAt"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  Warning: gh release view failed for {repo}@{tag}: {result.stderr}")
            return None

        data = json.loads(result.stdout)
        return data
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not fetch release details for {repo}@{tag}: {e}")
        return None


def match_asset(assets: List[Dict], pattern: str) -> Optional[Dict]:
    """Find an asset matching the given glob-like pattern."""
    # Convert simple glob pattern to regex
    regex_pattern = pattern.replace('.', r'\.').replace('*', '.*')
    regex = re.compile(regex_pattern, re.IGNORECASE)

    for asset in assets:
        if regex.match(asset.get('name', '')):
            return asset

    # Fallback: try to find any .elf or .bin file
    for asset in assets:
        name = asset.get('name', '')
        if name.endswith('.elf') or name.endswith('.bin'):
            return asset

    return None


def update_payload_from_github_release(payload_config: Dict, metadata: Dict) -> List[Dict]:
    """Update payload from GitHub releases using a two-step approach.
    
    Step 1: gh release list → get tagName, name, isPrerelease
    Step 2: gh release view TAG → get body, url, assets, createdAt
    """
    repo = payload_config['sourceRepo']
    pattern = payload_config.get('sourcePattern', '*.elf')
    versions = []
    
    # Preserve existing versions from metadata
    existing_versions = {v['version']: v for v in metadata.get('versions', [])}

    # Step 1: Get release list (tagName, name, isPrerelease only)
    releases = get_github_releases(repo)
    if not releases:
        print(f"  No releases found for {repo}, using existing metadata...")
        return metadata.get('versions', [])

    for i, release in enumerate(releases[:MAX_VERSIONS_PER_PAYLOAD]):
        tag = release.get('tagName', '')
        version = tag.lstrip('v')
        is_prerelease = release.get('isPrerelease', False)

        # Step 2: Get release details (body, url, assets, createdAt) via gh release view
        details = get_release_details(repo, tag)
        if not details:
            print(f"  No details found for {repo}@{tag}")
            continue

        body = details.get('body', '')
        created_at = details.get('createdAt', '')
        assets = details.get('assets', [])

        if not assets:
            print(f"  No assets found for {repo}@{tag}")
            continue

        matched = match_asset(assets, pattern)
        if not matched:
            print(f"  No matching asset for pattern '{pattern}' in {repo}@{tag}")
            continue

        file_name = matched['name']
        download_url = matched.get('url', '')
        if not download_url:
            download_url = f"https://github.com/{repo}/releases/download/{tag}/{file_name}"

        # Create version directory
        version_dir = PAYLOADS_DIR / payload_config['id'] / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = version_dir / file_name

        # Check if we already have this exact file
        file_hash = ""
        file_size = 0
        
        if dest_path.exists():
            existing_hash = calculate_file_hash(dest_path)
            existing_size = dest_path.stat().st_size
            print(f"  Already exists: {file_name}")
            file_hash = existing_hash
            file_size = existing_size
        else:
            try:
                file_hash, file_size = download_file(download_url, dest_path)
            except Exception as e:
                print(f"  Error downloading {file_name}: {e}")
                continue

        # Parse changelog
        changelog = parse_changelog(body)
        
        # Add pre-release warning to changelog if applicable
        if is_prerelease:
            changelog.insert(0, "⚠ This is a pre-release version. Use with caution.")

        versions.append({
            'version': version,
            'fileName': file_name,
            'filePath': f"payloads/{payload_config['id']}/{version}/{file_name}",
            'downloadUrl': download_url,
            'hash': file_hash,
            'fileSize': file_size,
            'releaseDate': created_at[:10] if created_at else '',
            'isDefault': i == 0,
            'isPreRelease': is_prerelease,
            'changelog': changelog
        })

    return versions


def update_payload_from_direct(payload_config: Dict, metadata: Dict) -> List[Dict]:
    """Update payload from direct URLs."""
    versions = []
    existing_versions = {v['version']: v for v in metadata.get('versions', [])}

    for ver_config in payload_config.get('manualVersions', []):
        file_name = ver_config['fileName']
        download_url = ver_config.get('url', '')
        version = ver_config['version']

        # Skip empty filenames (custom actions)
        if not file_name:
            versions.append({
                'version': version,
                'fileName': '',
                'filePath': '',
                'downloadUrl': download_url,
                'hash': '',
                'fileSize': 0,
                'releaseDate': ver_config.get('releaseDate', ''),
                'isDefault': ver_config.get('isDefault', False),
                'isPreRelease': False,
                'changelog': []
            })
            continue

        # Create version directory
        version_dir = PAYLOADS_DIR / payload_config['id'] / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = version_dir / file_name

        if dest_path.exists():
            existing_hash = calculate_file_hash(dest_path)
            existing_size = dest_path.stat().st_size
            print(f"  Already exists: {file_name}")
            versions.append({
                'version': version,
                'fileName': file_name,
                'filePath': f"payloads/{payload_config['id']}/{version}/{file_name}",
                'downloadUrl': download_url,
                'hash': existing_hash,
                'fileSize': existing_size,
                'releaseDate': ver_config.get('releaseDate', ''),
                'isDefault': ver_config.get('isDefault', False),
                'isPreRelease': False,
                'changelog': []
            })
        elif download_url:
            try:
                file_hash, file_size = download_file(download_url, dest_path)
                versions.append({
                    'version': version,
                    'fileName': file_name,
                    'filePath': f"payloads/{payload_config['id']}/{version}/{file_name}",
                    'downloadUrl': download_url,
                    'hash': file_hash,
                    'fileSize': file_size,
                    'releaseDate': ver_config.get('releaseDate', ''),
                    'isDefault': ver_config.get('isDefault', False),
                    'isPreRelease': False,
                    'changelog': []
                })
            except Exception as e:
                print(f"  Error downloading {file_name}: {e}")
                continue
        else:
            print(f"  No URL and file not found: {file_name}")

    return versions


def load_metadata(payload_id: str) -> Dict:
    """Load existing metadata.json for a payload."""
    metadata_path = PAYLOADS_DIR / payload_id / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_metadata(payload_id: str, metadata: Dict):
    """Save metadata.json for a payload."""
    metadata_path = PAYLOADS_DIR / payload_id / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)


def generate_payload_map_js(payloads_config: List[Dict]) -> str:
    """Generate the payload_map.js file content with v2 format."""

    lines = []
    lines.append("// @ts-check")
    lines.append("")
    lines.append(f"// Auto-generated by update_payloads.py on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append("// Do not edit manually - changes will be overwritten by GitHub Actions")
    lines.append("")
    lines.append(f'const CUSTOM_ACTION_APPCACHE_REMOVE = "{CUSTOM_ACTION_APPCACHE_REMOVE}";')
    lines.append("")

    # Type definitions
    lines.append("/**")
    lines.append(" * @typedef {Object} PayloadAuthor")
    lines.append(" * @property {string} name")
    lines.append(" * @property {string} [github]")
    lines.append(" * @property {string} [role]")
    lines.append(" */")
    lines.append("")
    lines.append("/**")
    lines.append(" * @typedef {Object} PayloadLicense")
    lines.append(" * @property {string} type")
    lines.append(" * @property {string} [url]")
    lines.append(" */")
    lines.append("")
    lines.append("/**")
    lines.append(" * @typedef {Object} PayloadVersion")
    lines.append(" * @property {string} version")
    lines.append(" * @property {string} fileName")
    lines.append(" * @property {string} filePath")
    lines.append(" * @property {string} downloadUrl")
    lines.append(" * @property {string} hash")
    lines.append(" * @property {number} fileSize")
    lines.append(" * @property {string} releaseDate")
    lines.append(" * @property {boolean} isDefault")
    lines.append(" * @property {boolean} isPreRelease")
    lines.append(" * @property {string[]} changelog")
    lines.append(" */")
    lines.append("")
    lines.append("/**")
    lines.append(" * @typedef {Object} PayloadInfo")
    lines.append(" * @property {string} id")
    lines.append(" * @property {string} displayTitle")
    lines.append(" * @property {string} description")
    lines.append(" * @property {string} author")
    lines.append(" * @property {PayloadAuthor[]} authors")
    lines.append(" * @property {string} projectUrl")
    lines.append(" * @property {PayloadLicense} license")
    lines.append(" * @property {string} sourceType")
    lines.append(" * @property {string} sourceRepo")
    lines.append(" * @property {PayloadVersion[]} versions")
    lines.append(" * @property {string[]} [supportedFirmwares]")
    lines.append(" * @property {number} [toPort]")
    lines.append(" * @property {string} [customAction]")
    lines.append(" * @property {boolean} visible")
    lines.append(" */")
    lines.append("")
    lines.append("/** @type {PayloadInfo[]} */")
    lines.append("const payload_map = [")

    for payload in payloads_config:
        # Load metadata for this payload
        metadata = load_metadata(payload['id'])
        license_info = metadata.get('license', {})
        
        # Format authors array
        authors = payload.get('authors', [])
        if isinstance(authors, str):
            # Convert comma-separated string to array
            authors = [a.strip() for a in authors.split(',')]
        
        authors_json = json.dumps([
            {"name": a, "github": f"https://github.com/{a}", "role": "Developer"}
            for a in authors
        ]) if authors else "[]"

        lines.append("    {")
        lines.append(f'        id: "{payload["id"]}",')
        lines.append(f'        displayTitle: "{payload["displayTitle"]}",')
        lines.append(f'        description: "{payload["description"]}",')
        lines.append(f'        author: "{", ".join(authors) if isinstance(authors, list) else authors}",')
        lines.append(f'        authors: {authors_json},')
        lines.append(f'        projectUrl: "{payload["projectUrl"]}",')
        lines.append(f'        license: {{type: "{license_info.get("type", "Unknown")}", url: "{license_info.get("url", "")}"}},')
        lines.append(f'        sourceType: "{payload["sourceType"]}",')
        lines.append(f'        sourceRepo: "{payload["sourceRepo"]}",')

        # versions array
        lines.append("        versions: [")
        for ver in payload.get('versions', []):
            lines.append("            {")
            lines.append(f'                version: "{ver["version"]}",')
            lines.append(f'                fileName: "{ver["fileName"]}",')
            lines.append(f'                filePath: "{ver.get("filePath", "")}",')
            lines.append(f'                downloadUrl: "{ver["downloadUrl"]}",')
            lines.append(f'                hash: "{ver["hash"]}",')
            lines.append(f'                fileSize: {ver["fileSize"]},')
            lines.append(f'                releaseDate: "{ver["releaseDate"]}",')
            lines.append(f'                isDefault: {"true" if ver["isDefault"] else "false"},')
            lines.append(f'                isPreRelease: {"true" if ver.get("isPreRelease", False) else "false"},')
            lines.append(f'                changelog: {json.dumps(ver.get("changelog", []))}')
            lines.append("            },")
        lines.append("        ],")

        # Optional fields
        if 'supportedFirmwares' in payload and payload['supportedFirmwares']:
            fw_json = json.dumps(payload['supportedFirmwares'])
            lines.append(f"        supportedFirmwares: {fw_json},")

        if 'toPort' in payload and payload['toPort']:
            lines.append(f"        toPort: {payload['toPort']},")

        if 'customAction' in payload and payload['customAction']:
            lines.append(f'        customAction: "{payload["customAction"]}",')

        lines.append("        visible: true")
        lines.append("    },")

    lines.append("];")
    lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("PS5 UMTX2 Payload Updater v2")
    print("=" * 60)

    # Ensure payloads directory exists
    PAYLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Load config
    if not PAYLOAD_CONFIG_FILE.exists():
        print(f"Error: Config file not found: {PAYLOAD_CONFIG_FILE}")
        sys.exit(1)

    with open(PAYLOAD_CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)

    has_changes = False

    for payload in config['payloads']:
        payload_id = payload['id']
        source_type = payload.get('sourceType', 'direct')

        print(f"\nProcessing: {payload['displayTitle']} ({payload_id}) [{source_type}]")

        # Load existing metadata
        metadata = load_metadata(payload_id)
        
        # Detect license
        license_info = detect_license(
            payload['sourceRepo'],
            payload.get('license', {})
        )
        metadata['license'] = license_info
        
        # Detect firmware compatibility
        firmware_compat = detect_firmware_compatibility(
            payload['sourceRepo'],
            payload.get('supportedFirmwares', [])
        )
        
        versions = []
        if source_type == 'github-release':
            versions = update_payload_from_github_release(payload, metadata)
        elif source_type == 'direct':
            versions = update_payload_from_direct(payload, metadata)
        elif source_type == 'custom':
            versions = update_payload_from_direct(payload, metadata)
        else:
            print(f"  Unknown source type: {source_type}")
            continue

        if not versions:
            print(f"  No versions found, keeping existing metadata")
            versions = metadata.get('versions', [])

        # Update metadata with all version info
        metadata['versions'] = versions
        metadata['supportedFirmwares'] = firmware_compat
        
        # Save updated metadata to metadata.json
        save_metadata(payload_id, metadata)
        
        payload['versions'] = versions
        payload['supportedFirmwares'] = firmware_compat
        
        print(f"  Found {len(versions)} version(s)")

    # Generate new payload_map.js
    new_content = generate_payload_map_js(config['payloads'])

    # Check if content changed
    if PAYLOAD_MAP_FILE.exists():
        with open(PAYLOAD_MAP_FILE, 'r') as f:
            old_content = f.read()

        # Normalize for comparison (ignore auto-generated timestamp)
        old_normalized = re.sub(
            r'// Auto-generated by update_payloads\.py on [^\n]+',
            '', old_content
        )
        new_normalized = re.sub(
            r'// Auto-generated by update_payloads\.py on [^\n]+',
            '', new_content
        )

        if old_normalized.strip() != new_normalized.strip():
            has_changes = True
            print("\nPayload map has changes - will update")
        else:
            print("\nNo changes in payload map")
    else:
        has_changes = True
        print("\nPayload map does not exist - will create")

    # Always write the file (updates timestamp)
    with open(PAYLOAD_MAP_FILE, 'w') as f:
        f.write(new_content)
    print(f"Written: {PAYLOAD_MAP_FILE}")

    # Set GitHub Actions output
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"has_changes={'true' if has_changes else 'false'}\n")

    print("\nDone!")
    return 0 if has_changes else 1


if __name__ == "__main__":
    sys.exit(main())
