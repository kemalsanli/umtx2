import os
import hashlib
import argparse
import re

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        data = f.read()
        sha256_hash.update(data)
    return sha256_hash.hexdigest()

def extract_default_versions_from_payload_map(directory_path):
    """Extract file paths of default versions from payload_map.js.
    
    Parses payload_map.js to find all version entries where isDefault: true,
    and returns a set of their filePath values for fast lookup during manifest
    generation. This reduces the appcache from ~40+ payload files to ~16
    (one default version per payload), cutting initial download size by ~60%.
    
    Args:
        directory_path: The directory containing payload_map.js
        
    Returns:
        set: A set of filePath strings for default versions.
             e.g. {"payloads/etahen/2.4b/etaHEN-2.4B.bin", ...}
    """
    payload_map_path = os.path.join(directory_path, "payload_map.js")
    if not os.path.exists(payload_map_path):
        return set()
    
    with open(payload_map_path, "r") as f:
        content = f.read()
    
    default_paths = set()
    
    # Find all version entries by matching filePath + isDefault proximity.
    # The changelog array can contain {} characters (e.g. unicode escapes like \u2605),
    # so the old [^{}]* pattern would break. Instead, we find each filePath line and
    # check if isDefault: true appears within a reasonable distance after it.
    for fp_match in re.finditer(r'filePath:\s*"([^"]*)"', content):
        # Look ahead from this position for isDefault: true (within ~500 chars)
        start = fp_match.end()
        lookahead = content[start:start + 500]
        if re.search(r'isDefault:\s*true', lookahead):
            default_paths.add(fp_match.group(1))
    
    return default_paths

def generate_cache_manifest(directory_path, include_payloads=True):
    manifest = ["CACHE MANIFEST"]
    manifest.append("")
    
    # Get the set of default version file paths from payload_map.js
    default_paths = extract_default_versions_from_payload_map(directory_path)
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            lower_file = file.lower()
            if lower_file.endswith('.appcache') or lower_file.endswith('.manifest') or lower_file.endswith('.exe') or lower_file.endswith('.py'):
                continue
            file_path = os.path.join(root, file)

            if not include_payloads and 'payload' in root:
                continue
            
            # Compute relative path for manifest entry
            rel_path = os.path.relpath(file_path, directory_path)
            rel_path = rel_path.replace("\\", "/")
            
            if 'payloads/' in rel_path and include_payloads:
                parts = rel_path.split("/")
                # payloads/{id}/{version}/{filename}
                if len(parts) >= 4 and parts[0] == "payloads":
                    
                    # Always include metadata.json files (small, needed for payload list)
                    if file == "metadata.json":
                        file_hash = calculate_file_hash(file_path)
                        manifest.append(rel_path + " #" + file_hash)
                        continue
                    
                    # For ELF/bin files: only include default versions
                    # Use case-insensitive comparison (macOS filesystem is case-insensitive)
                    if lower_file.endswith('.elf') or lower_file.endswith('.bin'):
                        rel_path_lower = rel_path.lower()
                        default_paths_lower = {p.lower() for p in default_paths}
                        if rel_path_lower not in default_paths_lower:
                            continue
            
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
args = parser.parse_args()

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
