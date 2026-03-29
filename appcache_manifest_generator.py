import os
import hashlib
import argparse
import json
import re

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        data = f.read()
        sha256_hash.update(data)
    return sha256_hash.hexdigest()

def load_payload_map(directory_path):
    """Load payload_map.js and extract payload version info for smart caching."""
    payload_map_path = os.path.join(directory_path, "payload_map.js")
    if not os.path.exists(payload_map_path):
        return {}
    
    with open(payload_map_path, "r") as f:
        content = f.read()
    
    # Extract all filePath entries from the payload_map
    # Match filePath: "payloads/..." patterns
    file_paths = re.findall(r'filePath:\s*"([^"]+)"', content)
    
    # Group by payload id: extract from path like "payloads/etahen/2.4b/etaHEN-2.4B.bin"
    payload_files = {}  # {payload_id: [filePath, ...]}
    for fp in file_paths:
        if not fp:
            continue
        parts = fp.split("/")
        if len(parts) >= 3 and parts[0] == "payloads":
            payload_id = parts[1]
            if payload_id not in payload_files:
                payload_files[payload_id] = []
            payload_files[payload_id].append(fp)
    
    return payload_files

def get_selected_versions_from_env():
    """
    In CI, this reads selected versions from environment variable or a config file.
    For now, returns empty dict meaning 'include all default versions'.
    
    When the PS5 browser generates the manifest client-side, it reads from localStorage.
    """
    # Check for environment variable with selected versions
    # Format: PAYLOAD_SELECTED_VERSIONS={"etahen":"2.4b","kstuff":"1.5",...}
    env_val = os.environ.get('PAYLOAD_SELECTED_VERSIONS', '')
    if env_val:
        try:
            return json.loads(env_val)
        except json.JSONDecodeError:
            pass
    return {}

def generate_cache_manifest(directory_path, include_payloads=True):
    manifest = ["CACHE MANIFEST"]
    manifest.append("")
    
    payload_files = load_payload_map(directory_path)
    selected_versions = get_selected_versions_from_env()
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            lower_file = file.lower()
            if lower_file.endswith('.appcache') or lower_file.endswith('.manifest') or lower_file.endswith('.exe') or lower_file.endswith('.py'): 
                continue
            file_path = os.path.join(root, file)

            if not include_payloads and 'payload' in root:
                continue
            
            # Smart payload caching: Only include selected/default version files
            rel_path = os.path.relpath(file_path, directory_path)
            rel_path = rel_path.replace("\\", "/")
            
            if 'payloads/' in rel_path and include_payloads:
                # Check if this file is inside a payload directory
                parts = rel_path.split("/")
                # payloads/{id}/{version}/{filename}
                if len(parts) >= 4 and parts[0] == "payloads":
                    payload_id = parts[1]
                    version = parts[2]
                    
                    # Always include metadata.json files (small, useful for debugging)
                    if file == "metadata.json":
                        file_hash = calculate_file_hash(file_path)
                        manifest.append(rel_path + " #" + file_hash)
                        continue
                    
                    # For ELF/bin files: check if this version is selected
                    if selected_versions and payload_id in selected_versions:
                        # Only include the selected version
                        if version != selected_versions[payload_id]:
                            continue
                    # If no selection info, include all (backward compatibility)
            
            file_hash = calculate_file_hash(file_path)
            
            if args.cloudflare_workaround and file == 'index.html':
                file_path = file_path.replace("index.html","")
                if file_path.isspace() or file_path == '':
                    file_path = '/'

            manifest_path = os.path.relpath(file_path, directory_path)
            if manifest_path.isspace() or manifest_path == '' or manifest_path == '.':
                manifest_path = '/'
                
            manifest_path = manifest_path.replace("\\","/")
            manifest.append(manifest_path + " #" + file_hash)

    manifest.append("")
    manifest.append("NETWORK:")
    manifest.append("*")

    return manifest

def update_manifest_tag(directory_path, add_manifest):
    index_html_path = os.path.join(directory_path, "index.html")
    if not os.path.exists(index_html_path):
        print(f"Couldn't find 'index.html' in '{directory_path}'. Skipping manifest tag update.")
        return

    index_html_needs_updating = False
    html_tag_found = False

    with open(index_html_path, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith("<html"):
                html_tag_found = True
                if add_manifest and "manifest" not in line:
                    lines[i] = "<html manifest=\"cache.appcache\">\n"
                    index_html_needs_updating = True
                elif not add_manifest and "manifest" in line:
                    lines[i] = "<html>\n"
                    index_html_needs_updating = True
                break

    if not html_tag_found:
        print(f"<html> tag not found in '{index_html_path}'")
    
    if index_html_needs_updating:
        with open(index_html_path, "w") as f:
            f.writelines(lines)
            action = "Added" if add_manifest else "Removed"
            print(f"{action} manifest attribute in '{index_html_path}'")

def oswalk_with_depth_limit(directory_path, max_depth):
    initial_depth = directory_path.rstrip(os.path.sep).count(os.path.sep)
    for root, dirs, files in os.walk(directory_path):
        yield root, dirs, files
        current_depth = root.count(os.path.sep)
        relative_depth = current_depth - initial_depth
        if relative_depth >= max_depth:
            del dirs[:]

parser = argparse.ArgumentParser(description="Generate an appcache file.")
parser.add_argument("-d", "--directory-path", nargs='?', default=None,
                    help="The directory to generate the appcache for. (default: find index.html in the current directory, up to 3 deep)")
parser.add_argument("-cf", "--cloudflare-workaround", action="store_true",
                    help="Cloudflare responds with 308 redirect to root when fetching index.html. Causing the appcache to error out.")
parser.add_argument("--update-manifest-tag", action="store_true", default=True,
                    help="Toggle updating the manifest tag in the HTML file (default: True).")
parser.add_argument("--clean", action="store_true",
                    help="Remove the previously generated cache manifest file and the manifest attribute from the HTML file.")
parser.add_argument("--selected-versions", type=str, default=None,
                    help="JSON string of selected versions for smart caching. Format: {\"etahen\":\"2.4b\",...}")
args = parser.parse_args()

# Handle selected versions from command line
if args.selected_versions:
    os.environ['PAYLOAD_SELECTED_VERSIONS'] = args.selected_versions

if args.directory_path is None:
    index_html_path = None
    for root, _, files in oswalk_with_depth_limit(os.getcwd(), 3):
        if 'index.html' in files:
            index_html_path = os.path.join(root, 'index.html')
            break
        
    if index_html_path is None:
        print("Couldn't find 'index.html' in the current directory or its subdirectories. Please provide a directory path with the -d flag.")
        exit(1)

    user_input = input(f"Found 'index.html' at '{os.path.dirname(index_html_path)}'. Do you want to use this directory? (y/n): ")

    if user_input.lower() != 'y':
        print("No directory path provided. Exiting.")
        exit(1)

    args.directory_path = os.path.dirname(index_html_path)

if args.update_manifest_tag:
    update_manifest_tag(args.directory_path, add_manifest=not args.clean)

if args.clean:
    output_path = os.path.join(args.directory_path, "cache.appcache")
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Removed cache manifest: '{output_path}'")
else:
    cache_manifest = generate_cache_manifest(args.directory_path)

    output_path = os.path.join(args.directory_path, "cache.appcache")
    output_path = output_path.replace("\\","/")

    with open(output_path, "w") as manifest_file:
        manifest_file.write("\n".join(cache_manifest))

    print(f"Cache manifest generated in path: '{output_path}'")
