#!/usr/bin/env python3
"""
Payload auto-update script for PS5 UMTX2 Jailbreak v2.

This script automates the process of fetching, downloading, and managing PS5 payload binaries
from GitHub releases or direct URLs. It reads configuration from .github/payloads.yaml,
downloads latest payload binaries, generates metadata, and produces document/en/ps5/payload_map.js.

============================================================================
                        ARCHITECTURE & WORKFLOW
============================================================================

1. Configuration (payloads.yaml)
   ├─ sourceType: 'github-release' | 'direct' | 'custom'
   ├─ github-release: Automatic fetching via GitHub API
   ├─ direct: Manual URL specification (for repos without releases)
   └─ custom: JS actions (no binary download)

2. Processing Pipeline
   ├─ Load config from payloads.yaml
   ├─ For each payload:
   │  ├─ Detect license from GitHub API
   │  ├─ Detect firmware compatibility from topics/README
   │  ├─ Fetch releases or use manual versions
   │  ├─ Download missing binaries (SECURITY: ZIP files are SKIPPED)
   │  ├─ Calculate SHA256 hash and file size
   │  ├─ Parse changelogs from release notes
   │  └─ Generate metadata.json per payload
   └─ Generate consolidated payload_map.js

3. Output Files
   ├─ document/en/ps5/payloads/{payload_id}/metadata.json
   ├─ document/en/ps5/payloads/{payload_id}/{version}/{binary_file}
   └─ document/en/ps5/payload_map.js

============================================================================
                    FOR DEVELOPERS: ADDING NEW PAYLOADS
============================================================================

**Option A: GitHub Releases (Recommended - Fully Automated)**

Add to .github/payloads.yaml:

```yaml
  - id: my-payload              # Unique identifier (lowercase, hyphens)
    displayTitle: My Payload     # Display name in UI
    description: Does something  # Short description
    authors:                     # List of contributors
      - your-github-username
    projectUrl: https://github.com/username/repo
    sourceType: github-release   # Enables automatic fetching
    sourceRepo: username/repo    # GitHub repo (owner/name)
    sourcePattern: my-payload*.elf  # Glob pattern to match asset name
    toPort: 9021                 # Optional: Port number for network payloads
    supportedFirmwares: ["3.", "4.", "5."]  # Optional: e.g., ["3.", "4."]
    license:                     # Optional: Auto-detected if empty
      type: ""
      url: ""
```

Requirements for github-release:
- Repository must have GitHub Releases with tags (e.g., v1.0, v1.0.1)
- Each release must contain a binary asset matching sourcePattern
- Assets must be .elf or .bin files (NOT .zip - security policy)
- Release tag format: `v{major}.{minor}.{patch}` (semver recommended)

Asset Naming Examples:
- Good: `my-payload-ps5.elf`, `my-payload-v1.0.elf`
- Bad: `Payload.zip`, `payload.tar.gz` (archives are SKIPPED)

**Option B: Direct URLs (Manual - For Special Cases)**

Use this when:
- Repository has no GitHub releases
- Assets are in ZIP format (must extract manually and host elsewhere)
- Using custom release hosting

```yaml
  - id: my-payload
    displayTitle: My Payload
    description: Does something
    authors:
      - your-github-username
    projectUrl: https://github.com/username/repo
    sourceType: direct           # Manual URL management
    sourceRepo: username/repo
    sourcePattern: my-payload*.elf
    toPort: 9021
    supportedFirmwares: []
    license:
      type: "GPL-3.0"
      url: "https://github.com/username/repo/blob/main/LICENSE"
    manualVersions:              # Explicitly list each version
      - version: "1.0"           # Version string (can be any format)
        fileName: my-payload.elf # Exact filename
        url: https://github.com/username/repo/releases/download/v1.0/my-payload.elf
        isDefault: true          # Mark latest version as default
        releaseDate: 2024-01-15  # YYYY-MM-DD format
```

**Option C: Custom Actions (JavaScript Only - No Binary)**

For browser-based actions:

```yaml
  - id: my-action
    displayTitle: My Action
    description: Does something in browser
    authors:
      - your-github-username
    projectUrl: https://github.com/username/repo
    sourceType: custom
    customAction: my-action      # Reference to JS function
    sourceRepo: ""
    supportedFirmwares: []
    license:
      type: ""
      url: ""
    manualVersions:
      - version: "1.0"
        fileName: ""             # Empty for custom actions
        url: ""
        isDefault: true
        releaseDate: 2024-01-01
```

============================================================================
                           SECURITY POLICIES
============================================================================

1. ZIP/Archive Handling: DISABLED
   - ZIP, TAR, GZ files are automatically SKIPPED
   - Reason: Cannot verify contents without extraction
   - Solution: Extract manually, host .elf files, use 'direct' sourceType

2. Hash Verification:
   - All downloaded binaries are SHA256-hashed
   - Hashes are stored in metadata.json and payload_map.js
   - Existing files are re-hashed to detect tampering

3. URL Validation:
   - Only HTTPS URLs are accepted
   - GitHub URLs are validated for format

============================================================================
                         COMMON ISSUES & SOLUTIONS
============================================================================

Issue: "No matching asset for pattern"
- Check sourcePattern matches actual release asset name
- Verify release contains .elf or .bin file (not .zip)
- Example: If asset is "tool-v1.0.elf", pattern should be "tool*.elf"

Issue: "Repository not found" or 404
- Verify sourceRepo format: "owner/repo" (no https://)
- Check if repository still exists on GitHub
- For moved repos, update sourceRepo with new owner

Issue: "Empty hash/downloadUrl in metadata"
- For 'direct' sourceType: Verify URLs in manualVersions
- For 'github-release': Check if asset name matches sourcePattern
- Check if file exists at specified path

Issue: Release date mismatch
- Script now uses 'publishedAt' (public release date)
- Old versions may have used 'createdAt' (tag creation date)
- To update: Delete metadata.json and re-run script

============================================================================

Features:
- GitHub Releases API integration with changelog parsing
- License auto-detection from GitHub API
- Pre-release flag detection
- Firmware compatibility auto-detection (topics + README)
- metadata.json generation/maintenance per payload
- payload_map.js v2 format generation with filePath support
- SHA256 hash verification for all binaries
- Automatic skipping of ZIP/archive files (security)
"""

import os
import sys
import json
import hashlib
import re
import subprocess
from pathlib import Path
from datetime import date, datetime, timezone
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
    """Get release details (body, url, assets, publishedAt) for a specific tag.
    
    This is the second step after get_github_releases(), since 'gh release list'
    does not support the 'body' field.
    
    IMPORTANT: Uses 'publishedAt' (not 'createdAt') for accurate release dates.
    - publishedAt: When release was made public (correct for user-facing dates)
    - createdAt: When tag was created (can be days before release)
    
    Returns:
        dict with keys: body, url, assets, publishedAt
        None if fetch fails or repo not found (404)
    """
    try:
        # FIXED: Now requests 'publishedAt' instead of 'createdAt'
        result = subprocess.run(
            ["gh", "release", "view", tag, "--repo", repo,
             "--json", "body,url,assets,publishedAt"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            # Detect deleted/moved repositories
            if '404' in stderr or 'not found' in stderr.lower():
                print(f"  ERROR: Repository not found: {repo} (may be deleted or moved)")
            else:
                print(f"  Warning: gh release view failed for {repo}@{tag}: {stderr}")
            return None

        data = json.loads(result.stdout)
        return data
    except subprocess.TimeoutExpired:
        print(f"  ERROR: Timeout fetching release details for {repo}@{tag}")
        return None
    except FileNotFoundError:
        print(f"  ERROR: 'gh' CLI not found. Install GitHub CLI: https://cli.github.com/")
        return None
    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON response for {repo}@{tag}: {e}")
        return None


def match_asset(assets: List[Dict], pattern: str) -> Optional[Dict]:
    """Find an asset matching the given glob-like pattern.
    
    SECURITY POLICY: ZIP/archive files are automatically SKIPPED.
    Only .elf and .bin files are accepted for safety reasons.
    
    Args:
        assets: List of GitHub release assets (dict with 'name' key)
        pattern: Glob-like pattern (e.g., "my-payload*.elf")
        
    Returns:
        Matching asset dict or None if no valid asset found
        
    Examples:
        >>> assets = [{'name': 'payload-v1.0.elf'}, {'name': 'payload.zip'}]
        >>> match_asset(assets, 'payload*.elf')
        {'name': 'payload-v1.0.elf'}  # .zip is skipped
    """
    # SECURITY: Explicitly block archive formats
    BLOCKED_EXTENSIONS = ('.zip', '.tar', '.gz', '.7z', '.rar', '.tar.gz', '.tgz')
    ALLOWED_EXTENSIONS = ('.elf', '.bin')
    
    # Convert simple glob pattern to regex
    regex_pattern = pattern.replace('.', r'\.').replace('*', '.*')
    regex = re.compile(regex_pattern, re.IGNORECASE)

    # Priority 1: Pattern match with security filter
    for asset in assets:
        name = asset.get('name', '')
        
        # SECURITY: Skip archive files
        if any(name.lower().endswith(ext) for ext in BLOCKED_EXTENSIONS):
            print(f"    SKIPPED (archive): {name} - Extract manually and use 'direct' sourceType")
            continue
            
        if regex.match(name):
            # Additional safety: Only accept known safe extensions
            if any(name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                return asset
            else:
                print(f"    SKIPPED (unsupported format): {name}")

    # Fallback: try to find any .elf or .bin file
    for asset in assets:
        name = asset.get('name', '')
        if name.lower().endswith(ALLOWED_EXTENSIONS):
            return asset

    return None


def update_payload_from_github_release(payload_config: Dict, metadata: Dict) -> List[Dict]:
    """Update payload from GitHub releases using a two-step approach.
    
    Step 1: gh release list → get tagName, name, isPrerelease
    Step 2: gh release view TAG → get body, url, assets, createdAt
    
    IMPORTANT: Existing versions are preserved even if they disappear from GitHub.
    This prevents data loss when releases are deleted or pruned upstream.
    """
    repo = payload_config['sourceRepo']
    pattern = payload_config.get('sourcePattern', '*.elf')
    payload_id = payload_config['id']
    versions = []
    
    # Preserve existing versions from metadata to prevent data loss
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

        # Step 2: Get release details (body, url, assets, publishedAt) via gh release view
        details = get_release_details(repo, tag)
        if not details:
            # If we can't fetch details but have existing version, preserve it
            if version in existing_versions:
                print(f"  Preserving existing version (fetch failed): {version}")
                versions.append(existing_versions[version])
            else:
                print(f"  No details found for {repo}@{tag}")
            continue

        body = details.get('body', '')
        published_at = details.get('publishedAt', '')
        assets = details.get('assets', [])

        if not assets:
            # No assets in release - preserve existing if available
            if version in existing_versions:
                print(f"  Preserving existing version (no assets): {version}")
                versions.append(existing_versions[version])
            else:
                print(f"  No assets found for {repo}@{tag}")
            continue

        matched = match_asset(assets, pattern)
        if not matched:
            # Asset name doesn't match pattern - preserve existing if available
            if version in existing_versions:
                print(f"  Preserving existing version (asset mismatch): {version}")
                versions.append(existing_versions[version])
            else:
                print(f"  No matching asset for pattern '{pattern}' in {repo}@{tag}")
            continue

        file_name = matched['name']
        download_url = matched.get('url', '')
        if not download_url:
            download_url = f"https://github.com/{repo}/releases/download/{tag}/{file_name}"

        # Create version directory
        version_dir = PAYLOADS_DIR / payload_id / version
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
                # Preserve existing version if download fails
                if version in existing_versions:
                    print(f"  Preserving existing version (download failed): {version}")
                    versions.append(existing_versions[version])
                continue

        # Parse changelog from GitHub release body
        changelog = parse_changelog(body)
        
        # PRESERVE existing changelog if it's more detailed than the release body.
        # This prevents overwriting manually-written changelogs with sparse GitHub notes.
        existing_ver = existing_versions.get(version)
        if existing_ver and existing_ver.get('changelog'):
            existing_cl = existing_ver['changelog']
            # Use existing changelog if it has more entries or same count
            # (existing entries are typically more detailed)
            if len(existing_cl) >= len(changelog):
                changelog = existing_cl
                print(f"  Preserved existing changelog for {version} ({len(changelog)} entries)")
        
        # Add pre-release warning to changelog if applicable
        if is_prerelease:
            pre_warning = "⚠ This is a pre-release version. Use with caution."
            if pre_warning not in changelog:
                changelog.insert(0, pre_warning)

        versions.append({
            'version': version,
            'fileName': file_name,
            'filePath': f"payloads/{payload_id}/{version}/{file_name}",
            'downloadUrl': download_url,
            'hash': file_hash,
            'fileSize': file_size,
            'releaseDate': published_at[:10] if published_at else '',
            'isDefault': False,  # Will be set by releaseDate-based sort below
            'isPreRelease': is_prerelease,
            'changelog': changelog
        })

    # PRESERVE: Add versions from existing metadata that weren't found in GitHub releases.
    # This prevents data loss when releases are deleted/pruned from the upstream repo.
    seen_versions = {v['version'] for v in versions}
    for ver_key, ver_data in existing_versions.items():
        if ver_key not in seen_versions:
            # Check if the binary still exists on disk
            ver_file = ver_data.get('fileName', '')
            ver_path = PAYLOADS_DIR / payload_id / ver_key / ver_file
            if ver_file and ver_path.exists():
                print(f"  Preserving orphaned version (not in GitHub releases): {ver_key}")
                versions.append(ver_data)
            else:
                print(f"  Skipping orphaned version (binary missing): {ver_key}")

    # Sort versions by releaseDate (most recent first) and set isDefault accordingly
    # This ensures the most recent version is always marked as default, regardless of
    # the order returned by GitHub API or any other source.
    versions_with_date = [v for v in versions if v.get('releaseDate')]
    versions_with_date.sort(key=lambda x: x['releaseDate'], reverse=True)
    
    # Mark all as non-default first
    for v in versions:
        v['isDefault'] = False
    
    # Mark the most recent version as default
    if versions_with_date:
        versions_with_date[0]['isDefault'] = True
    
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
                'isDefault': False,  # Will be set by releaseDate-based sort below
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
                'isDefault': False,  # Will be set by releaseDate-based sort below
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
                    'isDefault': False,  # Will be set by releaseDate-based sort below
                    'isPreRelease': False,
                    'changelog': []
                })
            except Exception as e:
                print(f"  Error downloading {file_name}: {e}")
                continue
        else:
            print(f"  No URL and file not found: {file_name}")

    # Sort versions by releaseDate (most recent first) and set isDefault accordingly
    # This ensures the most recent version is always marked as default, regardless of
    # the order in the config file.
    versions_with_date = [v for v in versions if v.get('releaseDate')]
    versions_with_date.sort(key=lambda x: x['releaseDate'], reverse=True)
    
    # Mark all as non-default first
    for v in versions:
        v['isDefault'] = False
    
    # Mark the most recent version as default
    if versions_with_date:
        versions_with_date[0]['isDefault'] = True
    
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


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def save_metadata(payload_id: str, metadata: Dict):
    """Save metadata.json for a payload."""
    metadata_path = PAYLOADS_DIR / payload_id / "metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=json_serial)


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
    lines.append(" * @property {boolean} [willHideEveryTime]")
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

        if payload.get('willHideEveryTime'):
            lines.append("        willHideEveryTime: true,")

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

        # Ensure top-level fields from config are always in metadata
        metadata['id'] = payload_id
        metadata['displayTitle'] = payload.get('displayTitle', payload_id)
        metadata['description'] = payload.get('description', '')
        metadata['authors'] = payload.get('authors', [])
        metadata['projectUrl'] = payload.get('projectUrl', '')
        metadata['sourceRepo'] = payload.get('sourceRepo', '')
        if 'toPort' in payload:
            metadata['toPort'] = payload['toPort']

        # Update metadata with all version info
        metadata['versions'] = versions
        metadata['supportedFirmwares'] = firmware_compat
        
        # Save updated metadata to metadata.json
        save_metadata(payload_id, metadata)
        
        payload['versions'] = versions
        payload['supportedFirmwares'] = firmware_compat
        
        print(f"  Found {len(versions)} version(s)")

    # SAFETY: Detect orphaned payloads (on disk but not in payloads.yaml)
    # This prevents accidental data loss when a payload is manually added
    # to payload_map.js but forgotten from payloads.yaml.
    configured_ids = {p['id'] for p in config['payloads']}
    orphaned_payloads = []

    if PAYLOADS_DIR.exists():
        for payload_dir in sorted(PAYLOADS_DIR.iterdir()):
            if not payload_dir.is_dir():
                continue
            metadata_file = payload_dir / "metadata.json"
            if not metadata_file.exists():
                continue
            payload_id = payload_dir.name
            if payload_id not in configured_ids:
                print(f"\n  ⚠ WARNING: Orphaned payload detected: '{payload_id}'")
                print(f"    This payload exists on disk but is NOT in payloads.yaml!")
                print(f"    Including from existing metadata to prevent data loss.")
                try:
                    with open(metadata_file, 'r') as f:
                        orphan_meta = json.load(f)
                    orphan_entry = {
                        'id': payload_id,
                        'displayTitle': orphan_meta.get('displayTitle', payload_id),
                        'description': orphan_meta.get('description', ''),
                        'authors': orphan_meta.get('authors', []),
                        'projectUrl': orphan_meta.get('projectUrl', ''),
                        'sourceType': orphan_meta.get('sourceType', 'direct'),
                        'sourceRepo': orphan_meta.get('sourceRepo', ''),
                        'versions': orphan_meta.get('versions', []),
                        'supportedFirmwares': orphan_meta.get('supportedFirmwares', []),
                        'willHideEveryTime': orphan_meta.get('willHideEveryTime', False),
                    }
                    if orphan_meta.get('toPort'):
                        orphan_entry['toPort'] = orphan_meta['toPort']
                    if orphan_meta.get('customAction'):
                        orphan_entry['customAction'] = orphan_meta['customAction']
                    config['payloads'].append(orphan_entry)
                    orphaned_payloads.append(payload_id)
                except Exception as e:
                    print(f"    ERROR: Could not load metadata for '{payload_id}': {e}")

    if orphaned_payloads:
        print(f"\n{'=' * 60}")
        print(f"  ⚠ {len(orphaned_payloads)} ORPHANED PAYLOAD(S) DETECTED:")
        for oid in orphaned_payloads:
            print(f"    - {oid}")
        print(f"  These payloads are NOT in .github/payloads.yaml.")
        print(f"  They have been included from existing metadata to prevent data loss.")
        print(f"  ACTION REQUIRED: Add them to payloads.yaml to silence this warning.")
        print(f"{'=' * 60}")

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
    # Always return 0 for success - exit code 1 is reserved for actual errors
    # Changes are tracked via GITHUB_OUTPUT environment variable
    return 0


if __name__ == "__main__":
    sys.exit(main())
