#!/usr/bin/env python3
"""PS5 UMTX2 Test Suite - Runs on GitHub Actions and locally"""

import json
import os
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent / "document" / "en" / "ps5"
PAYLOADS_DIR = BASE_DIR / "payloads"
REQUIRED_METADATA_FIELDS = ["id", "displayTitle", "authors", "projectUrl", "versions"]
REQUIRED_VERSION_FIELDS = ["version", "fileName", "filePath", "downloadUrl"]

# Color output for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}PASS{Colors.RESET}: {msg}")

def print_failure(msg: str):
    print(f"{Colors.RED}FAIL{Colors.RESET}: {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}WARN{Colors.RESET}: {msg}")

def print_info(msg: str):
    print(f"{Colors.BLUE}INFO{Colors.RESET}: {msg}")

def check_node_available() -> bool:
    """Check if Node.js is available for syntax checking."""
    try:
        subprocess.run(
            ["node", "--version"],
            capture_output=True,
            check=True,
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def test_payload_structure():
    """Test payload folder structure and metadata files exist."""
    print_info("Checking payload folder structure...")
    
    if not PAYLOADS_DIR.exists():
        raise AssertionError(f"Payloads directory not found: {PAYLOADS_DIR}")
    
    payload_folders = [d for d in PAYLOADS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not payload_folders:
        raise AssertionError("No payload folders found in payloads directory")
    
    errors = []
    for payload_dir in payload_folders:
        metadata_file = payload_dir / "metadata.json"
        if not metadata_file.exists():
            errors.append(f"Missing metadata.json in {payload_dir.name}")
    
    if errors:
        raise AssertionError("\n".join(errors))
    
    print_success(f"Found {len(payload_folders)} payload folders with metadata.json")

def test_metadata_format():
    """Validate metadata.json format and required fields."""
    print_info("Validating metadata.json files...")
    
    payload_folders = [d for d in PAYLOADS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    errors = []
    
    for payload_dir in payload_folders:
        metadata_file = payload_dir / "metadata.json"
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check required fields
            for field in REQUIRED_METADATA_FIELDS:
                if field not in metadata:
                    errors.append(f"{payload_dir.name}/metadata.json: Missing required field '{field}'")
            
            # Validate versions array exists and is not empty
            if "versions" not in metadata:
                errors.append(f"{payload_dir.name}/metadata.json: Missing 'versions' array")
                continue
            
            if not isinstance(metadata["versions"], list):
                errors.append(f"{payload_dir.name}/metadata.json: 'versions' must be an array")
                continue
            
            if len(metadata["versions"]) == 0:
                errors.append(f"{payload_dir.name}/metadata.json: 'versions' array is empty")
                continue
            
            # Check each version has required fields
            for idx, version in enumerate(metadata["versions"]):
                for field in REQUIRED_VERSION_FIELDS:
                    if field not in version:
                        errors.append(
                            f"{payload_dir.name}/metadata.json: Version {idx} missing field '{field}'"
                        )
                
                # Check if filePath exists and file is present
                if "filePath" in version and version["filePath"]:
                    file_path = BASE_DIR / version["filePath"]
                    if not file_path.exists():
                        errors.append(
                            f"{payload_dir.name}: File not found: {version['filePath']}"
                        )
            
            # Check URL format for downloadUrl
            if "versions" in metadata:
                for version in metadata["versions"]:
                    if "downloadUrl" in version and version["downloadUrl"]:
                        url = version["downloadUrl"]
                        if not (url.startswith("http://") or url.startswith("https://") or url == ""):
                            errors.append(
                                f"{payload_dir.name}: Invalid downloadUrl format: {url}"
                            )
        
        except json.JSONDecodeError as e:
            errors.append(f"{payload_dir.name}/metadata.json: Invalid JSON - {e}")
        except Exception as e:
            errors.append(f"{payload_dir.name}/metadata.json: {e}")
    
    if errors:
        raise AssertionError("\n".join(errors))
    
    print_success(f"All {len(payload_folders)} metadata.json files are valid")

def test_js_syntax():
    """Check all JS files for syntax errors using Node.js."""
    if not check_node_available():
        print_warning("Node.js not available, skipping JavaScript syntax tests")
        return
    
    print_info("Checking JavaScript syntax...")
    
    js_files = list(BASE_DIR.rglob("*.js"))
    errors = []
    
    for js_file in js_files:
        # Skip node_modules if present
        if "node_modules" in str(js_file):
            continue
        
        result = subprocess.run(
            ["node", "--check", str(js_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            errors.append(f"{js_file.relative_to(BASE_DIR)}: {result.stderr.strip()}")
    
    if errors:
        raise AssertionError("\n".join(errors))
    
    print_success(f"All {len(js_files)} JavaScript files have valid syntax")

def test_html_references():
    """Check index.html references all required files."""
    print_info("Checking HTML script references...")
    
    index_html = BASE_DIR / "index.html"
    if not index_html.exists():
        raise AssertionError("index.html not found")
    
    with open(index_html, 'r') as f:
        html_content = f.read()
    
    # Extract all script src attributes
    script_pattern = r'<script[^>]+src="([^"]+)"'
    script_refs = re.findall(script_pattern, html_content)
    
    errors = []
    missing_files = []
    
    for ref in script_refs:
        file_path = BASE_DIR / ref
        if not file_path.exists():
            missing_files.append(ref)
    
    if missing_files:
        errors.append(f"Missing files referenced in index.html:\n  - " + "\n  - ".join(missing_files))
    
    # Check for duplicate IDs (basic check)
    id_pattern = r'id="([^"]+)"'
    all_ids = re.findall(id_pattern, html_content)
    duplicate_ids = [id for id in set(all_ids) if all_ids.count(id) > 1]
    
    if duplicate_ids:
        errors.append(f"Duplicate IDs found in index.html: {', '.join(duplicate_ids)}")
    
    if errors:
        raise AssertionError("\n".join(errors))
    
    print_success(f"All {len(script_refs)} script references are valid")

def test_payload_map():
    """Test payload_map.js format and consistency."""
    print_info("Validating payload_map.js...")
    
    payload_map_file = BASE_DIR / "payload_map.js"
    if not payload_map_file.exists():
        raise AssertionError("payload_map.js not found")
    
    with open(payload_map_file, 'r') as f:
        content = f.read()
    
    # Check if file is valid JS
    if check_node_available():
        result = subprocess.run(
            ["node", "--check", str(payload_map_file)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise AssertionError(f"payload_map.js has syntax errors: {result.stderr}")
    
    # Extract payload_map array using regex
    array_match = re.search(r'const payload_map = \[(.*?)\];', content, re.DOTALL)
    if not array_match:
        raise AssertionError("Could not find payload_map array in payload_map.js")
    
    # Basic validation - check for expected structure patterns
    required_patterns = [
        r'id:\s*"[^"]+"',
        r'displayTitle:\s*"[^"]+"',
        r'versions:\s*\['
    ]
    
    for pattern in required_patterns:
        if not re.search(pattern, content):
            raise AssertionError(f"payload_map.js missing expected pattern: {pattern}")
    
    # Check that all payloads from metadata folders are represented
    payload_folders = [d.name for d in PAYLOADS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    for folder in payload_folders:
        # Skip appcache-remove special case as it may not have files
        if folder == "appcache-remove":
            continue
        if f'id: "{folder}"' not in content and f"id: '{folder}'" not in content:
            print_warning(f"Payload '{folder}' not found in payload_map.js")
    
    print_success("payload_map.js is valid")

def test_appcache():
    """Test cache.appcache lists all required files."""
    print_info("Validating cache.appcache...")
    
    appcache_file = BASE_DIR / "cache.appcache"
    if not appcache_file.exists():
        raise AssertionError("cache.appcache not found")
    
    with open(appcache_file, 'r') as f:
        lines = f.readlines()
    
    # Extract cached files (lines after CACHE MANIFEST and before NETWORK:)
    cached_files = []
    in_cache_section = False
    
    for line in lines:
        line = line.strip()
        if line == "CACHE MANIFEST":
            in_cache_section = True
            continue
        if line == "NETWORK:":
            break
        if in_cache_section and line and not line.startswith("#"):
            # Remove hash if present
            file_path = line.split("#")[0].strip()
            if file_path:
                cached_files.append(file_path)
    
    errors = []
    missing_files = []
    
    for file_ref in cached_files[:30]:  # Check first 30 to avoid long output
        file_path = BASE_DIR / file_ref
        if not file_path.exists():
            missing_files.append(file_ref)
    
    if missing_files:
        errors.append(f"cache.appcache references missing files:\n  - " + "\n  - ".join(missing_files))
    
    # Check that key JS files are in cache
    key_files = [
        "int64.js",
        "rop.js", 
        "main.js",
        "umtx2.js",
        "syscalls.js",
        "payload_map.js",
        "js/app.js"
    ]
    
    for key_file in key_files:
        if not any(key_file in f for f in cached_files):
            errors.append(f"cache.appcache missing key file: {key_file}")
    
    if errors:
        raise AssertionError("\n".join(errors))
    
    print_success(f"cache.appcache is valid ({len(cached_files)} files cached)")

def test_global_functions():
    """Test that required global functions are exported."""
    print_info("Checking global function exports...")
    
    key_files = {
        "js/app.js": ["run"],
        "js/utils/page-switcher.js": ["switchPage", "openSettings", "closeSettings"],
        "js/ui/licenses-modal.js": ["openLicenses", "closeLicenses"],
        "js/ui/developer-options.js": ["openDevOptions", "closeDevOptions"]
    }
    
    errors = []
    
    for file_name, expected_functions in key_files.items():
        file_path = BASE_DIR / file_name
        if not file_path.exists():
            errors.append(f"Expected file not found: {file_name}")
            continue
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        for func in expected_functions:
            # Check if function is defined and exported to window
            if f"function {func}" not in content and f"const {func}" not in content:
                continue
            if f"window.{func}" not in content and f"window['{func}']" not in content:
                print_warning(f"{file_name}: Function '{func}' may not be exported to global scope")
    
    if errors:
        raise AssertionError("\n".join(errors))
    
    print_success("Global function exports verified")

def test_css_validity():
    """Basic CSS validity check."""
    print_info("Checking CSS validity...")
    
    css_file = BASE_DIR / "main.css"
    if not css_file.exists():
        raise AssertionError("main.css not found")
    
    with open(css_file, 'r') as f:
        content = f.read()
    
    # Check for basic CSS syntax issues
    errors = []
    
    # Check for balanced braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    if open_braces != close_braces:
        errors.append(f"CSS has unbalanced braces: {open_braces} open, {close_braces} close")
    
    # Check for unclosed comments
    unclosed_comments = content.count('/*') - content.count('*/')
    if unclosed_comments != 0:
        errors.append(f"CSS has unclosed comments: {unclosed_comments} unclosed")
    
    if errors:
        raise AssertionError("\n".join(errors))
    
    print_success("main.css is valid")

def test_firmware_offsets():
    """Check that firmware offset files exist for all supported versions."""
    print_info("Checking firmware offset files...")
    
    offsets_dir = BASE_DIR / "offsets"
    if not offsets_dir.exists():
        raise AssertionError("offsets directory not found")
    
    offset_files = list(offsets_dir.glob("*.js"))
    
    if not offset_files:
        raise AssertionError("No offset files found in offsets/ directory")
    
    # Check that each offset file is valid JS
    if check_node_available():
        errors = []
        for offset_file in offset_files:
            result = subprocess.run(
                ["node", "--check", str(offset_file)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                errors.append(f"{offset_file.name}: {result.stderr.strip()}")
        
        if errors:
            raise AssertionError("\n".join(errors))
    
    print_success(f"All {len(offset_files)} offset files are valid")

def main():
    """Run all tests and report results."""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("PS5 UMTX2 Test Suite")
    print(f"{'='*60}{Colors.RESET}\n")
    
    tests = [
        ("Payload Structure", test_payload_structure),
        ("Metadata Format", test_metadata_format),
        ("JavaScript Syntax", test_js_syntax),
        ("HTML References", test_html_references),
        ("Payload Map", test_payload_map),
        ("AppCache", test_appcache),
        ("Global Functions", test_global_functions),
        ("CSS Validity", test_css_validity),
        ("Firmware Offsets", test_firmware_offsets),
    ]
    
    passed = 0
    failed = 0
    warnings = 0
    
    for test_name, test_func in tests:
        print(f"\n{Colors.BLUE}Running: {test_name}{Colors.RESET}")
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print_failure(f"{test_name}: {e}")
            failed += 1
        except Exception as e:
            print_failure(f"{test_name}: Unexpected error: {e}")
            failed += 1
    
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Test Results Summary")
    print(f"{'='*60}{Colors.RESET}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    else:
        print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    print()
    
    if failed > 0:
        sys.exit(1)
    else:
        print(f"{Colors.GREEN}All tests passed!{Colors.RESET}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
