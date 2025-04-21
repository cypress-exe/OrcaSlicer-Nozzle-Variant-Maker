#!/usr/bin/env python3
"""
🎨 OrcaSlicer Nozzle Variant Maker

A friendly tool for creating nozzle size variants in OrcaSlicer filament profiles.
"""

import os
import sys
import json
import shutil
import time
import uuid
import logging
import platform
from pathlib import Path
from typing import List, Tuple, Dict

# Constants
DEFAULT_PROFILE_DIR = Path(os.getenv('APPDATA', '')) / 'OrcaSlicer' / 'user'
LOG_DIR_NAME = 'logs'
BACKUP_PREFIX = 'backup_'
MAX_LOG_FILES = 10
MAX_PREVIEW_GROUPS = 3
MAX_PREVIEW_VARIANTS = 3
LINE_DELAY = 0.1  # Seconds between output lines

# Type Aliases
UserProfile = Tuple[str, Path]  # (user_id, filament_base_path)
ProfileGroups = Dict[str, List[str]]  # Base material to list of variants


class NozzleConversionError(Exception):
    """Base exception for nozzle conversion errors."""
    pass


def delayed_print(*args, **kwargs):
    """Print with slight delay and extra spacing at the start of each line."""
    time.sleep(LINE_DELAY)

    # Set default separator and end if not provided
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')

    # Join the arguments using the separator
    output = sep.join(str(arg) for arg in args)

    # Add a space before each line
    spaced_output = '\n'.join(' ' + line for line in output.split('\n'))

    print(spaced_output, end=end)


def print_header(text: str):
    """Print formatted section header with extended underline."""
    header_length = len(text) + 5
    delayed_print(f"\n{text}")
    delayed_print("=" * header_length)
    logging.info(f"PROCESSING STAGE: {text.upper()}")


def setup_logging(script_dir: Path) -> Path:
    """Configure comprehensive logging system."""
    logs_dir = script_dir / LOG_DIR_NAME
    logs_dir.mkdir(exist_ok=True, parents=True)

    # Rotate log files
    existing_logs = sorted(logs_dir.glob("*.log"), key=os.path.getmtime)
    while len(existing_logs) >= MAX_LOG_FILES:
        oldest = existing_logs.pop(0)
        oldest.unlink()

    log_file = logs_dir / f"orca_nozzle_{time.strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)-8s] %(message)s',
        handlers=[logging.FileHandler(log_file, encoding='utf-8')]
    )

    logger = logging.getLogger()
    logger.info("=== SYSTEM CONFIGURATION ===")
    logger.info(f"Python Version: {platform.python_version()}")
    logger.info(f"System OS: {platform.system()} {platform.release()}")
    logger.info(f"OS Version: {platform.version()}")
    logger.info(f"Machine Architecture: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Script Directory: {script_dir}")
    logger.info(f"Log File: {log_file}")
    logger.info("=== LOGGING INITIALIZED ===")
    
    return log_file


def get_profile_groups(profile_dir: Path) -> ProfileGroups:
    """Organize profiles into grouped material variants."""
    logging.debug(f"Scanning profile directory: {profile_dir}")
    groups = {}
    try:
        for f in profile_dir.glob('*.json'):
            parts = f.stem.split('@')
            base_material = parts[0].strip()
            variant = parts[1].strip() if len(parts) > 1 else 'default'
            groups.setdefault(base_material, []).append(variant)
            logging.debug(f"Found profile: {f.name} -> {base_material}/{variant}")
        
        for material in groups:
            groups[material].sort(key=lambda x: [float(y) for y in x.split() if y.replace('.','').isdigit()])
            logging.debug(f"Sorted variants for {material}: {groups[material]}")
        
        logging.info(f"Discovered {len(groups)} material groups with {sum(len(v) for v in groups.values())} profiles")
        return groups
    except Exception as e:
        logging.error(f"Error scanning profiles: {str(e)}", exc_info=True)
        raise


def format_group_preview(groups: ProfileGroups) -> str:
    """Create human-readable preview of profile groups."""
    preview = []
    for material, variants in list(groups.items())[:MAX_PREVIEW_GROUPS]:
        variants_display = ', '.join(variants[:MAX_PREVIEW_VARIANTS])
        if len(variants) > MAX_PREVIEW_VARIANTS:
            variants_display += f" (+{len(variants)-MAX_PREVIEW_VARIANTS})"
        preview.append(f"  🌡️ {material}: {variants_display}")
    
    if len(groups) > MAX_PREVIEW_GROUPS:
        preview.append(f"  📁 ... and {len(groups)-MAX_PREVIEW_GROUPS} more materials")
    
    return '\n'.join(preview)


def find_user_profiles(base_dir: Path) -> List[UserProfile]:
    """Discover all user profiles with valid filament configurations."""
    logging.info(f"Searching for user profiles in: {base_dir}")
    users = []
    try:
        for user_dir in base_dir.iterdir():
            if not user_dir.is_dir():
                continue
            filament_base = user_dir / 'filament' / 'base'
            if filament_base.is_dir():
                logging.info(f"Found user profile: {user_dir.name}")
                users.append((user_dir.name, filament_base))
        
        if not users:
            logging.warning("No valid user profiles found")
            raise NozzleConversionError("🔍 No user profiles found")
        
        logging.info(f"Found {len(users)} user profiles")
        return users
    except FileNotFoundError as e:
        logging.error(f"Directory not found: {e.filename}", exc_info=True)
        raise NozzleConversionError(f"❌ Directory not found: {base_dir}") from e


def validate_nozzle_size(size: str) -> bool:
    """Ensure nozzle size follows standard format."""
    valid = size.replace('.', '', 1).isdigit()
    logging.debug(f"Nozzle size validation: {size} -> {'valid' if valid else 'invalid'}")
    return valid


def select_user_profile(users: List[UserProfile]) -> UserProfile:
    """Interactive profile selection with detailed previews."""
    logger = logging.getLogger()
    if len(users) == 1:
        logger.info("Auto-selecting single user profile")
        delayed_print(f"\n🔍 Using profile: {users[0][0]}")
        return users[0]

    print_header("USER PROFILES")
    logger.info("Presenting user profile selection")
    
    for idx, (user_id, profile_dir) in enumerate(users, 1):
        groups = get_profile_groups(profile_dir)
        delayed_print(f"\n[{idx}] 📂 {user_id}")
        delayed_print(f"  🧪 Materials: {len(groups)}")
        delayed_print(f"  📄 Profiles: {sum(len(v) for v in groups.values())}")
        delayed_print(format_group_preview(groups))

    while True:
        choice = input("\n 👉 Select profile number or 'v'+number for details (q to quit): ").strip().lower()
        logger.info(f"User selection: {choice}")
        
        if choice == 'q':
            logger.info("User quit during profile selection")
            raise KeyboardInterrupt()
        
        if choice.startswith('v'):
            try:
                user_idx = int(choice[1:]) - 1
                user_id, profile_dir = users[user_idx]
                logger.info(f"Displaying details for profile index {user_idx}")
                groups = get_profile_groups(profile_dir)
                delayed_print(f"\n📂 All Profiles for {user_id}:")
                for material, variants in groups.items():
                    delayed_print(f"\n  🧪 {material}:")
                    for var in variants:
                        delayed_print(f"    - {var}")
            except (ValueError, IndexError):
                logger.warning(f"Invalid view selection: {choice}")
                delayed_print("⚠️ Invalid selection. Use format 'v2' to view details")
        
        elif choice.isdigit():
            user_idx = int(choice) - 1
            if 0 <= user_idx < len(users):
                selected = users[user_idx]
                logger.info(f"Selected profile: {selected[0]}")
                return selected
            logger.warning(f"Invalid profile number: {choice}")
            delayed_print("⚠️ Invalid number. Try again.")
        
        else:
            logger.warning(f"Invalid input: {choice}")
            delayed_print("⚠️ Please enter a number or 'v'+number")


def backup_profiles(profile_base: Path) -> Path:
    """Create timestamped backup of profile directory."""
    logger = logging.getLogger()
    try:
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_dir = profile_base.parent / f"{BACKUP_PREFIX}{timestamp}"
        logger.info(f"Creating backup in: {backup_dir}")
        
        shutil.copytree(profile_base, backup_dir)
        profile_count = len(list(profile_base.glob('*.json')))
        
        logger.info(f"Backup complete. {profile_count} profiles archived")
        delayed_print(f"""
🔐 Safety Backup Created
─────────────────────────
• Location: {backup_dir}
• Profiles archived: {profile_count}
• To restore: 
  1. Close OrcaSlicer
  2. Delete '{profile_base.name}' folder
  3. Rename '{backup_dir.name}' to '{profile_base.name}'
  4. Restart OrcaSlicer""")
        
        return backup_dir
    except Exception as e:
        logger.error("Backup failed", exc_info=True)
        raise NozzleConversionError("Backup creation failed") from e


def modify_profile_data(data: dict, source_size: str, target_size: str) -> dict:
    """Update profile data with new nozzle size."""
    logger = logging.getLogger()
    try:
        modified = data.copy()
        original_name = data.get('name', '')
        modified['name'] = original_name.replace(source_size, target_size)
        logger.debug(f"Renamed profile: {original_name} → {modified['name']}")
        
        if 'compatible_printers' in modified:
            original_printers = modified['compatible_printers']
            modified['compatible_printers'] = [
                printer.replace(source_size, target_size)
                for printer in original_printers
            ]
            logger.debug(f"Updated printers: {original_printers} → {modified['compatible_printers']}")
        
        original_id = data.get('filament_settings_id', [''])[0]
        new_id = f"PFUS{uuid.uuid4().hex[:16]}"
        modified['filament_settings_id'] = [new_id]
        logger.debug(f"Generated new ID: {original_id} → {new_id}")
        
        return modified
    except Exception as e:
        logger.error("Profile modification failed", exc_info=True)
        raise


def process_profiles(profile_base: Path, source_size: str, target_size: str) -> dict:
    """Batch process profiles for nozzle conversion."""
    logger = logging.getLogger()
    results = {'success': 0, 'skipped': 0, 'errors': 0}
    
    try:
        profile_files = list(profile_base.glob(f"*{source_size}*.json"))
        logger.info(f"Found {len(profile_files)} profiles matching '{source_size}'")
        
        if not profile_files:
            raise NozzleConversionError(f"🔍 No profiles found matching '{source_size}' nozzle size")
        
        print_header(f"CONVERTING {len(profile_files)} PROFILES")
        logger.info("Starting profile conversion process")
        
        for profile_path in profile_files:
            try:
                logger.debug(f"Processing: {profile_path.name}")
                
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                new_data = modify_profile_data(data, source_size, target_size)
                new_path = profile_path.parent / profile_path.name.replace(source_size, target_size)
                
                if new_path.exists():
                    results['skipped'] += 1
                    logger.warning(f"Skipping existing file: {new_path.name}")
                    delayed_print(f"⏩ Skipped existing: {new_path.name}")
                    continue
                
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2)
                
                results['success'] += 1
                logger.info(f"Created new profile: {new_path.name}")
                delayed_print(f"✅ Created: {new_path.name}")
            
            except json.JSONDecodeError as e:
                logger.error(f"JSON error in {profile_path.name}", exc_info=True)
                results['errors'] += 1
                delayed_print(f"❌ Error processing: {profile_path.name}")
            
            except Exception as e:
                logger.error(f"Unexpected error with {profile_path.name}", exc_info=True)
                results['errors'] += 1
                delayed_print(f"❌ Error processing: {profile_path.name}")
        
        logger.info(f"Conversion results: {results}")
        return results
    
    except Exception as e:
        logger.error("Fatal error during conversion", exc_info=True)
        raise


def main():
    """Main execution flow with comprehensive logging."""
    script_dir = Path(__file__).parent.resolve()
    log_file = setup_logging(script_dir)
    
    print(f"""
 🐋 OrcaSlicer Nozzle Variant Maker
 ===================================

 🔧 Before continuing:
 1. Close OrcaSlicer completely
 2. Ensure your printer is not active
 
 📝 Log file: {log_file}
""")
    input(" 🔼 Press Enter to begin...")
    logging.info("===== SESSION STARTED =====")
    
    try:
        print_header("LOCATING PROFILES")
        base_dir = DEFAULT_PROFILE_DIR
        logging.info(f"Using default profile directory: {base_dir}")
        
        while not base_dir.exists():
            delayed_print("\n🔍 Default profile directory not found")
            custom_path = input(" 👉 Enter OrcaSlicer 'user' directory path: ").strip()
            base_dir = Path(custom_path).expanduser()
            logging.info(f"User provided directory: {base_dir}")
        
        users = find_user_profiles(base_dir)
        user_id, profile_base = select_user_profile(users)
        logging.info(f"Selected profile base: {profile_base}")

        print_header("NOZZLE CONFIGURATION")
        logging.info("Starting nozzle size configuration")
        
        while True:
            source_size = input(" 👉 Enter SOURCE nozzle size to copy (e.g. 0.4): ").strip()
            logging.debug(f"Source size input: {source_size}")
            if validate_nozzle_size(source_size):
                break
            delayed_print("⚠️ Invalid format. Use numbers like 0.4 or 0.6")
        
        while True:
            target_size = input(" 👉 Enter TARGET nozzle size to create (e.g. 0.8): ").strip()
            logging.debug(f"Target size input: {target_size}")
            if validate_nozzle_size(target_size) and target_size != source_size:
                break
            delayed_print("⚠️ Must be different from source and numeric")
        
        logging.info(f"Nozzle conversion configured: {source_size} → {target_size}")

        print_header("CREATING BACKUP")
        backup_profiles(profile_base)
        
        print_header("CONVERSION PROGRESS")
        results = process_profiles(profile_base, source_size, target_size)
        
        print_header("CONVERSION RESULTS")
        delayed_print(f"""
✅ Success: {results['success']}
⏩ Skipped: {results['skipped']}
❌ Errors:  {results['errors']}

🔄 Please restart OrcaSlicer to see changes
""")
        logging.info("===== SUCCESSFUL COMPLETION =====")
    
    except NozzleConversionError as e:
        logging.error("Fatal error occurred", exc_info=True)
        delayed_print(f"\n❌ Error: {str(e)}")
        delayed_print(f"📝 See log for details: {log_file}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("User interrupted operation")
        delayed_print("\n🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.critical("Unexpected error", exc_info=True)
        delayed_print(f"\n⚠️ Unexpected error: {str(e)}")
        delayed_print(f"📝 See log for details: {log_file}")
        sys.exit(1)


if __name__ == '__main__':
    main()