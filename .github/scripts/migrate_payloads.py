#!/usr/bin/env python3
"""
Migration script to convert flat payload structure to organized folder structure.
This script moves existing payload files into {id}/{version}/ directories and creates metadata.json.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Mapping from current flat files to new structure
MIGRATION_MAP = [
    {
        "id": "etahen",
        "current": "etaHEN-2.4B.bin",
        "version": "2.4b",
        "displayTitle": "etaHEN",
        "description": "AIO HEN",
        "authors": ["LightningMods", "Buzzer", "sleirsgoevy", "ChendoChap", "astrelsky", "illusion", "CTN", "SiSTR0", "Nomadic"],
        "projectUrl": "https://github.com/etaHEN/etaHEN",
        "sourceRepo": "etaHEN/etaHEN",
        "supportedFirmwares": ["3.", "4.", "5."],
        "toPort": 9021,
    },
    {
        "id": "kstuff",
        "current": "kstuff.elf",
        "version": "1.5",
        "displayTitle": "ps5-kstuff",
        "description": "FPKG enabler",
        "authors": ["sleirsgoevy", "john-tornblom", "EchoStretch", "buzzer-re", "idlesauce", "BestPig", "LightningMods", "zecoxao"],
        "projectUrl": "https://github.com/EchoStretch/ps4jb-payloads/",
        "sourceRepo": "EchoStretch/ps4jb-payloads",
        "supportedFirmwares": ["3.", "4.", "5."],
        "toPort": 9021,
    },
    {
        "id": "byepervisor",
        "current": "byepervisor.elf",
        "version": "d89a105",
        "displayTitle": "Byepervisor HEN",
        "description": "FPKG enabler",
        "authors": ["SpecterDev", "ChendoChap", "flatz", "fail0verflow", "Znullptr", "kiwidog", "sleirsgoevy", "EchoStretch", "LightningMods", "BestPig", "zecoxao", "TheOfficialFloW"],
        "projectUrl": "https://github.com/EchoStretch/Byepervisor",
        "sourceRepo": "EchoStretch/Byepervisor",
        "supportedFirmwares": ["1.00", "1.01", "1.02", "1.12", "1.14", "2.00", "2.20", "2.25", "2.26", "2.30", "2.50", "2.70"],
        "toPort": 9021,
    },
    {
        "id": "libhijacker",
        "current": "libhijacker-game-patch.v1.160.elf",
        "version": "1.160",
        "displayTitle": "libhijacker game-patch",
        "description": "Patches supported games to run at higher framerates, and adds debug menus to certain titles.",
        "authors": ["illusion0001", "astrelsky"],
        "projectUrl": "https://github.com/illusion0001/libhijacker",
        "sourceRepo": "illusion0001/libhijacker-game-patch",
        "supportedFirmwares": ["3.", "4."],
        "toPort": None,
    },
    {
        "id": "websrv",
        "current": "websrv-ps5.elf",
        "version": "0.28.1",
        "displayTitle": "websrv",
        "description": "Custom homebrew loader. Runs on port 8080.",
        "authors": ["john-tornblom"],
        "projectUrl": "https://github.com/ps5-payload-dev/websrv",
        "sourceRepo": "ps5-payload-dev/websrv",
        "supportedFirmwares": [],
        "toPort": 9021,
    },
    {
        "id": "ftpsrv",
        "current": "ftpsrv-ps5.elf",
        "version": "0.14.3",
        "displayTitle": "ftpsrv",
        "description": "FTP server. Runs on port 2121.",
        "authors": ["john-tornblom"],
        "projectUrl": "https://github.com/ps5-payload-dev/ftpsrv",
        "sourceRepo": "ps5-payload-dev/ftpsrv",
        "supportedFirmwares": [],
        "toPort": 9021,
    },
    {
        "id": "klogsrv",
        "current": "klogsrv-ps5.elf",
        "version": "0.7.1",
        "displayTitle": "klogsrv",
        "description": "Klog server. Runs on port 3232.",
        "authors": ["john-tornblom"],
        "projectUrl": "https://github.com/ps5-payload-dev/klogsrv",
        "sourceRepo": "ps5-payload-dev/klogsrv",
        "supportedFirmwares": [],
        "toPort": 9021,
    },
    {
        "id": "shsrv",
        "current": "shsrv-ps5.elf",
        "version": "0.18",
        "displayTitle": "shsrv",
        "description": "Telnet shell server. Runs on port 2323.",
        "authors": ["john-tornblom"],
        "projectUrl": "https://github.com/ps5-payload-dev/shsrv",
        "sourceRepo": "ps5-payload-dev/shsrv",
        "supportedFirmwares": [],
        "toPort": 9021,
    },
    {
        "id": "gdbsrv",
        "current": "gdbsrv-ps5.elf",
        "version": "0.7.1",
        "displayTitle": "gdbsrv",
        "description": "GDB server. Runs on port 2159.",
        "authors": ["john-tornblom"],
        "projectUrl": "https://github.com/ps5-payload-dev/gdbsrv",
        "sourceRepo": "ps5-payload-dev/gdbsrv",
        "supportedFirmwares": [],
        "toPort": 9021,
    },
    {
        "id": "ps5debug",
        "current": "ps5debug_v1.0b5.elf",
        "version": "1.0b5",
        "displayTitle": "ps5debug",
        "description": "Debugger",
        "authors": ["SiSTR0", "ctn123"],
        "projectUrl": "https://github.com/GoldHEN/ps5debug",
        "sourceRepo": "GoldHEN/ps5debug",
        "supportedFirmwares": ["3.", "4.", "5."],
        "toPort": 9021,
    },
    {
        "id": "ps5debug-dizz",
        "current": "ps5debug_dizz.elf",
        "version": "0.0.1-r2",
        "displayTitle": "ps5debug",
        "description": "Debugger, open source version by DizzRL",
        "authors": ["Dizz", "astrelsky", "John Tornblom", "SiSTR0", "golden", "idlesauce"],
        "projectUrl": "https://github.com/idlesauce/ps5debug",
        "sourceRepo": "idlesauce/ps5debug",
        "supportedFirmwares": [],
        "toPort": 9021,
    },
    {
        "id": "kstuff-toggle",
        "current": "kstuff-toggle.elf",
        "version": "0.2",
        "displayTitle": "kstuff-toggle",
        "description": "Kstuff Toggle Beta",
        "authors": ["EchoStretch", "john-tornblom"],
        "projectUrl": "https://github.com/EchoStretch/kstuff-toggle",
        "sourceRepo": "EchoStretch/kstuff-toggle",
        "supportedFirmwares": ["3.", "4.", "5."],
        "toPort": 9021,
    },
    {
        "id": "ps5-versions",
        "current": "ps5-versions.elf",
        "version": "1.0",
        "displayTitle": "ps5-versions",
        "description": "Shows kernel build, os and sdk versions",
        "authors": ["SiSTRo"],
        "projectUrl": "https://github.com/SiSTR0/ps5-versions",
        "sourceRepo": "SiSTR0/ps5-versions",
        "supportedFirmwares": ["1.", "2.", "3.", "4."],
        "toPort": None,
    },
    {
        "id": "rp-get-pin",
        "current": "rp-get-pin.elf",
        "version": "0.1.1",
        "displayTitle": "ps5-remoteplay-get-pin",
        "description": "Get Remote Play PIN for offline activated users. Send again to cancel.",
        "authors": ["idlesauce"],
        "projectUrl": "https://github.com/idlesauce/ps5-remoteplay-get-pin",
        "sourceRepo": "idlesauce/ps5-remoteplay-get-pin",
        "supportedFirmwares": [],
        "toPort": 9021,
    },
    {
        "id": "elfldr",
        "current": "elfldr-ps5.elf",
        "version": "latest",
        "displayTitle": "ELF Loader",
        "description": "ELF loader",
        "authors": ["john-tornblom"],
        "projectUrl": "https://github.com/ps5-payload-dev/elfldr",
        "sourceRepo": "ps5-payload-dev/elfldr",
        "supportedFirmwares": [],
        "toPort": None,
    },
]


def migrate_payloads(payloads_dir: Path, dry_run: bool = False):
    """Migrate payloads to new folder structure."""
    
    print("=" * 60)
    print("PS5 UMTX2 Payload Migration Script")
    print("=" * 60)
    print()
    
    if dry_run:
        print("DRY RUN MODE - No files will be modified")
        print()
    
    if not payloads_dir.exists():
        print(f"Error: Payloads directory not found: {payloads_dir}")
        return False
    
    migrated_count = 0
    skipped_count = 0
    
    for payload in MIGRATION_MAP:
        payload_id = payload["id"]
        current_file = payload["current"]
        version = payload["version"]
        
        print(f"Processing: {payload['displayTitle']} ({payload_id})")
        
        # Source file
        source_path = payloads_dir / current_file
        if not source_path.exists():
            print(f"  ⚠ Warning: Source file not found: {current_file}")
            skipped_count += 1
            continue
        
        # Destination structure
        dest_dir = payloads_dir / payload_id / version
        dest_file = dest_dir / current_file
        metadata_file = payloads_dir / payload_id / "metadata.json"
        
        # Check if already migrated
        if dest_file.exists():
            print(f"  ✓ Already migrated: {current_file}")
            skipped_count += 1
            continue
        
        if not dry_run:
            # Create directories
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file (not move, in case something goes wrong)
            shutil.copy2(source_path, dest_file)
            print(f"  ✓ Copied: {current_file} → {payload_id}/{version}/{current_file}")
            
            # Calculate file size and hash
            file_size = dest_file.stat().st_size
            
            # Create metadata.json
            metadata = {
                "id": payload_id,
                "displayTitle": payload["displayTitle"],
                "description": payload["description"],
                "authors": payload["authors"],
                "projectUrl": payload["projectUrl"],
                "sourceRepo": payload["sourceRepo"],
                "supportedFirmwares": payload["supportedFirmwares"],
                "toPort": payload["toPort"],
                "versions": [
                    {
                        "version": version,
                        "fileName": current_file,
                        "filePath": f"payloads/{payload_id}/{version}/{current_file}",
                        "downloadUrl": "",  # Will be filled by update script
                        "hash": "",  # Will be filled by update script
                        "fileSize": file_size,
                        "releaseDate": "",  # Will be filled by update script
                        "isDefault": True,
                        "isPreRelease": False,
                        "changelog": []
                    }
                ]
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"  ✓ Created: metadata.json")
        else:
            print(f"  → Would copy: {current_file} → {payload_id}/{version}/{current_file}")
            print(f"  → Would create: {payload_id}/metadata.json")
        
        migrated_count += 1
        print()
    
    print("=" * 60)
    print(f"Migration Summary:")
    print(f"  Migrated: {migrated_count}")
    print(f"  Skipped: {skipped_count}")
    print("=" * 60)
    
    if not dry_run:
        print()
        print("⚠ IMPORTANT: Old flat files are still in place.")
        print("   Please verify the migration, then manually delete them.")
        print("   Or run: python .github/scripts/cleanup_old_payloads.py")
    
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Migrate payloads to new folder structure")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--payloads-dir", type=str, default="document/en/ps5/payloads",
                        help="Path to payloads directory (default: document/en/ps5/payloads)")
    args = parser.parse_args()
    
    # Resolve paths relative to repo root
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    payloads_dir = repo_root / args.payloads_dir
    
    success = migrate_payloads(payloads_dir, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
