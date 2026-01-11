# ⚡ UltraSpeed Copy - Smart File Transfer System

<div align="center">

![Version](https://img.shields.io/badge/version-2.1-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Production-grade file transfer system with modern animated GUI, network device support, and intelligent automation**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Device Support](#-device-support) • [Screenshots](#-screenshots)

</div>

---

## 🚀 Overview

UltraSpeed Copy is a powerful Windows file transfer system that combines the reliability of ROBOCOPY with a beautiful modern interface. It supports **PC-to-PC**, **PC-to-Device**, **Device-to-PC**, and **Network transfers** with automatic optimization.

### ✨ Key Highlights

- 🎨 **Modern Animated UI** - Dark theme with smooth 30 FPS animations
- 🌐 **Network Device Support** - Easy connection to phones, tablets, NAS, and other PCs
- 🔧 **Auto-Thread Detection** - Intelligently adjusts based on your hardware
- 📊 **Live Dashboard** - Real-time speed, progress, and statistics
- ⚡ **Multi-threaded** - Up to 128 threads for maximum performance
- 🔄 **Smart Modes** - Full copy, incremental, or mirror sync
- 📱 **Universal** - Supports local drives, USB, network paths (UNC), and SMB shares

---

## 🎯 Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Multi-threaded Copy** | 1-128 configurable threads with auto-detection |
| **Copy Modes** | Full Copy, Incremental (only new/changed), Mirror Sync |
| **Network Support** | PC ↔ PC, PC ↔ Phone/Tablet, PC ↔ NAS, PC ↔ External Device |
| **Resume Support** | Automatically resume interrupted transfers |
| **Compression** | Optional ZIP/TAR.GZ compression before transfer |
| **Task Scheduler** | Automated daily/weekly backups |
| **Performance Tracking** | Real-time speed monitoring and historical statistics |

### Modern UI Features

- 🎨 **Dark Professional Theme** - Reduced eye strain
- 📊 **Animated Stat Cards** - Speed, Files, Data, Progress with smooth transitions
- 📋 **Syntax-Highlighted Logs** - Color-coded activity log
- 🔧 **Auto-Thread Adjustment** - Hardware-aware optimization
- 🌐 **Device Browser** - Easy selection of local/network/USB devices
- 💫 **Smooth Animations** - Professional feel with 30 FPS updates

---

## 📸 Screenshots

### Main Interface
*Modern dark theme with two-column layout and animated dashboard*

```
┌──────────────────────────────────────────────────────────────┐
│ ⚡ UltraSpeed Copy                             ● Ready       │
│    Smart Copy & Sync System - Modern Edition                 │
├──────────────────────────────────────────────────────────────┤
│ Configuration              │  Live Dashboard                 │
│ ├─ Paths                   │  ┌────────┐  ┌────────┐       │
│ ├─ Options                 │  │⚡Speed │  │📄Files │       │
│ ├─ Controls                │  └────────┘  └────────┘       │
│                            │  ┌────────┐  ┌────────┐       │
│                            │  │💾Data  │  │📈Progress│      │
│                            │  └────────┘  └────────┘       │
│                            │  Activity Log                  │
└──────────────────────────────────────────────────────────────┘
```

<!-- Add actual screenshots once available -->
<!-- ![Main Interface](images/main-interface.png) -->

### Device Selection
*Browse dialog with Local Drives, Network Devices, and USB/External tabs*

<!-- ![Device Selection](images/device-selection.png) -->

---

## 📦 Installation

### Requirements

- **OS**: Windows 10 (1809+) or Windows 11
- **Python**: 3.8 or higher
- **Memory**: 2 GB minimum, 4 GB+ recommended
- **Disk Space**: 100 MB for application

### Quick Install

```powershell
# 1. Clone or download repository
git clone https://github.com/yourusername/ultraspeed-copy.git
cd ultraspeed-copy

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch application
python gui/app_modern.py
```

### Dependencies

```txt
psutil>=5.9.0         # System resource monitoring (required)
ttkbootstrap>=1.10.1  # Modern UI theme (required)
matplotlib>=3.5.0     # Charts and visualization (optional)
numpy>=1.21.0         # Required by matplotlib (optional)
```

---

## 🎮 Usage

### Quick Start

1. **Launch Application**
   ```powershell
   python gui/app_modern.py
   ```

2. **Select Source**
   - Click "Browse" next to Source
   - Choose from: Local Drives / Network Devices / USB-External
   - Enter UNC path for network devices (e.g., `\\192.168.1.100\SharedFolder`)

3. **Select Destination**
   - Click "Browse" next to Destination
   - Choose target location

4. **Configure Options**
   - **Copy Mode**: Full / Incremental / Mirror
   - **Threads**: Auto-detected (or manual adjustment)
   - **Network Optimization**: Auto-enabled for UNC paths
   - **Compression**: Optional for text-heavy data

5. **Start Copy**
   - Click "▶ Start Copy"
   - Watch animated dashboard update in real-time
   - Monitor speed, files, and progress

### Copy Modes Explained

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Full Copy** | Copies all files | Initial backup, archiving |
| **Incremental** | Only new/changed files | Daily backups, quick updates |
| **Mirror Sync** | Exact replica (⚠️ deletes extra) | Server sync, exact copies |

---

## 🌐 Device Support

### Supported Transfer Types

✅ **PC to PC**
```
\\DESKTOP-PC\Users\Public → C:\Backup
```

✅ **PC to Phone/Tablet** (via SMB/Network)
```
C:\Photos → \\PHONE-NAME\Internal Storage
```

✅ **PC to NAS**
```
C:\Documents → \\192.168.1.100\Backup
```

✅ **PC to USB/External Drive**
```
C:\Data → E:\Backup
```

✅ **Device to PC**
```
\\TABLET\SDCard → D:\FromTablet
```

✅ **Network to Network**
```
\\NAS1\Share → \\NAS2\Backup
```

### Network Device Connection

#### Method 1: Browse Dialog
1. Click "Browse" button
2. Go to "🌐 Network Devices" tab
3. Enter UNC path: `\\DeviceName\Path` or `\\192.168.1.X\Path`
4. Click "Connect to Network Path"

#### Method 2: Manual Entry
- Directly type UNC path in Source/Destination field
- Format: `\\hostname\sharename` or `\\IP\sharename`

### Common Device Paths

| Device | Path Format | Example |
|--------|-------------|---------|
| **Windows PC** | `\\hostname\sharename` | `\\DESKTOP-PC\Users\Public` |
| **Android Phone** | `\\devicename\storage` | `\\PHONE\Internal Storage` |
| **iPhone/iPad** | Via iTunes/iCloud | Use file sharing apps |
| **NAS** | `\\IP\sharename` | `\\192.168.1.100\backup` |
| **Linux Samba** | `\\IP\sharename` | `\\192.168.1.50\home` |

---

## ⚙️ Advanced Features

### Auto-Thread Detection

The system automatically detects your hardware and calculates optimal thread count:

```
High-end (16+ cores, 16+ GB RAM, SSD):  32 threads
Mid-range (8 cores, 8+ GB RAM, SSD):    16 threads
Basic (4 cores, 4+ GB RAM):              8 threads
Network transfers:                       Automatically reduced
```

Toggle "Auto-adjust" to enable/disable automatic optimization.

### Task Scheduler Automation

Create automated backups:

```powershell
# Run as Administrator
cd scheduler
.\quick_setup.bat

# Or use PowerShell directly
.\register_task.ps1 -Interactive
```

Schedule options:
- Daily at specific time
- Weekly on specific days
- Custom schedules

### Compression

Enable compression for:
- ✅ Text files, logs, source code
- ✅ Documents and spreadsheets
- ❌ Images, videos (already compressed)
- ❌ Real-time sync scenarios

---

## 📊 Performance

### Benchmarks

| Scenario | Expected Speed | Configuration |
|----------|----------------|---------------|
| **SSD to SSD (local)** | 300-500 MB/s | 32-64 threads |
| **HDD to HDD (local)** | 80-120 MB/s | 8-16 threads |
| **PC to USB 3.0** | 100-200 MB/s | 16-32 threads |
| **PC to Gigabit NAS** | 80-110 MB/s | 16-32 threads |
| **PC to WiFi Device** | 20-50 MB/s | 8-16 threads |

*Actual speeds vary based on hardware and network conditions*

### System Requirements vs Performance

| System Type | Recommended Threads | Expected Performance |
|-------------|---------------------|---------------------|
| High-end workstation | 32-64 | Maximum speed |
| Gaming PC | 16-32 | Excellent |
| Standard laptop | 8-16 | Very good |
| Budget PC | 4-8 | Good |

---

## 🔧 Configuration

### Auto-Thread Adjustment

**Enable (default):**
- System detects hardware capabilities
- Adjusts based on transfer type (local vs network)
- Shows `"XX threads (optimal)"` label

**Disable:**
- Uncheck "Auto-adjust" toggle
- Manually set thread count with slider
- Shows `"XX threads (manual)"` label

### Network Optimization

Automatically enabled when:
- UNC paths detected (`\\server\share`)
- Mapped network drives identified
- Destination is network location

Features:
- Restartable mode (resume capability)
- Enhanced retry logic
- Optimized buffer sizes

---

## 📝 Command Line Usage

### Run Modern UI

```powershell
# Standard launch
python gui/app_modern.py

# Without deprecation warnings
python -W ignore::DeprecationWarning gui/app_modern.py

# Using batch launcher
.\run_modern.bat
```

### Original UI (Basic)

```powershell
python gui/app.py
# or
.\run.bat
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue: "Module not found" errors**
```powershell
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue: Network device not accessible**
```
Solution:
1. Ensure network sharing is enabled on device
2. Check firewall settings (allow SMB port 445)
3. Verify credentials if prompted
4. Try IP address instead of hostname
```

**Issue: Slow transfer speed**
```
Solution:
1. Reduce thread count for HDDs
2. Disable compression for large files
3. Check network bandwidth
4. Verify antivirus isn't scanning during copy
```

**Issue: GUI not themed (looks plain)**
```powershell
# Solution: Install ttkbootstrap
pip install --upgrade ttkbootstrap
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```powershell
# Clone repository
git clone https://github.com/yourusername/ultraspeed-copy.git
cd ultraspeed-copy

# Install development dependencies
pip install -r requirements.txt

# Run in development mode
python gui/app_modern.py
```

### Coding Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Test on Windows 10 and 11
- Update README for new features

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ROBOCOPY** - Microsoft's robust file copy utility
- **ttkbootstrap** - Modern themed tkinter widgets
- **psutil** - Cross-platform system monitoring
- **matplotlib** - Data visualization library

---

## 📞 Support

### Documentation

- **This README** - Quick start and features
- **images/README.md** - Screenshot guidelines
- **scheduler/** - Task automation scripts
- **config/config.json** - Configuration options

### Getting Help

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review logs in `logs/` directory
3. Check device network sharing settings
4. Open an issue on GitHub

---

## 🗺️ Roadmap

### Planned Features

- [ ] Bandwidth throttling
- [ ] Email notifications
- [ ] Cloud storage integration (OneDrive, Google Drive)
- [ ] Multi-language support
- [ ] Web-based remote monitoring
- [ ] Encryption support
- [ ] File deduplication
- [ ] Advanced filtering rules

---

## 📈 Project Stats

![GitHub repo size](https://img.shields.io/github/repo-size/yourusername/ultraspeed-copy)
![GitHub issues](https://img.shields.io/github/issues/yourusername/ultraspeed-copy)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/ultraspeed-copy)
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/ultraspeed-copy)

---

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

<div align="center">

**Made with ❤️ for seamless file transfers**

[⬆ Back to Top](#-ultraspeed-copy---smart-file-transfer-system)

</div>
