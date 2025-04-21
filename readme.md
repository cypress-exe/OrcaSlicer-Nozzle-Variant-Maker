# 🐋 OrcaSlicer Nozzle Variant Maker

A user-friendly tool for batch-creating nozzle size variants in OrcaSlicer filament profiles.

![Header](./images/header-image.png)

![Demo](./images/example-usage.png)

## ✨ Features

- 🔍 Auto-discovers OrcaSlicer profiles
- 💾 Automatic backups before making changes
- 📝 Detailed logging for troubleshooting
- ♻️ Non-destructive operation (never modifies originals)
- 🎮 Interactive command-line interface
- 🚦 Safety checks and validations
- 📁 Supports multiple user configurations

## 📦 Installation

1. **Requirements**:
   - Python 3.6+
   - OrcaSlicer installed

2. **Download**:
   ```bash
   git clone https://github.com/cypress-exe/orcaslicer-nozzle-variant-maker.git
   cd orcaslicer-nozzle-variant-maker
   ```

## 🚀 Usage

1. **Close OrcaSlicer** ⚠️ - Required to prevent conflicts!

2. **Run the tool**:
   ```bash
   python3 orcaslicer_nozzle_variant_maker.py
   ```

3. **Follow the prompts**:
   ```
   1️⃣ Press Enter to begin
   2️⃣ Select profile directory (if not auto-detected)
   3️⃣ Choose user configuration (if not auto-detected)
   4️⃣ Enter source nozzle size (existing)
   5️⃣ Enter target nozzle size (new)
   6️⃣ Let the tool create backups and new profiles
   ```

4. **Restart OrcaSlicer** to see new profiles

## 🛠️ How It Works

1. **Profile Discovery**:
   - Scans `user/*/filament/base` directories
   - Groups profiles by material type
   - Shows variant counts (0.4mm, 0.6mm, etc)

2. **Safety Backup**:
   - Creates timestamped `backup_YYYYMMDD_HHMMSS`
   - Copies all JSON profiles
   - Provides restore instructions

3. **Profile Conversion**:
   - Creates new `[material] @ [size].json` files
   - Updates compatible printers list
   - Generates new unique IDs

4. **Logging**:
   - Stores detailed logs in `logs/`
   - Keeps last 10 log files
   - Records system info for debugging

## 🔒 Safety Features

- 🛑 Never modifies existing profiles
- 💾 Mandatory backups before changes
- ✅ Input validation for nozzle sizes
- 🔄 Atomic file operations
- 📁 Original files remain untouched

## 🚨 Troubleshooting

Common Issues:
- **Profile directory not found**  
  Verify OrcaSlicer's installation path
- **No profiles detected**  
  Ensure you have existing nozzle profiles
- **JSON errors**  
  Check log files in `logs/` directory

Logs contain:
- Full error stack traces
- System configuration
- Operation timestamps
- File paths and modifications

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

**Happy Printing!** If you enjoy this tool, please consider starring the repo ⭐