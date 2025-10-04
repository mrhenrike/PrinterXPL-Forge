# PrinterReaper v1.0 - Release Notes

## 🎉 First Major Release of PrinterReaper!

### 🚀 Key Features

- **🔍 Automatic Language Detection**: Automatically detects supported printer languages (PJL/PS/PCL)
- **🌐 HTTP Fallback**: When port 9100 is not accessible, automatically tries HTTP connections
- **🔄 Smart Retry Logic**: Improved timeout handling with automatic retry mechanisms
- **📊 Enhanced Logging**: Structured logging for better debugging and analysis
- **🎯 OSINT Integration**: Built-in passive reconnaissance capabilities
- **🔒 CVE Lookup**: Automatic vulnerability database queries
- **⚡ Performance Optimized**: Faster detection and connection establishment

### 🛠️ Technical Improvements

- **Multiple Connection Methods**: Port 9100, HTTP, IPP support
- **Connection Manager**: Intelligent fallback between connection methods
- **HTTP Connector**: Full support for web-based printers
- **Language Detector**: Automatic detection of printer capabilities
- **Enhanced Error Handling**: Robust retry logic and timeout management
- **Structured Logging**: Advanced debugging and analysis capabilities

### 📋 Breaking Changes

- **Renamed**: From VOID-PRINT to PrinterReaper
- **License**: Changed from GPL-2.0 to MIT License
- **Branding**: Complete cleanup of all legacy references
- **Documentation**: Comprehensive updates throughout

### 🎯 Usage

```bash
# Automatic language detection (recommended)
python src/main.py <target> auto

# Manual language specification
python src/main.py <target> pjl
python src/main.py <target> ps
python src/main.py <target> pcl
```

### 📊 Tested Targets

- ✅ 201.55.111.98 (Port 9100 access)
- ✅ 76.235.10.242 (Port 9100 access)  
- ✅ 99.158.42.49 (HTTP fallback)

### 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper

# Install dependencies
pip install -r requirements.txt

# Run PrinterReaper
python src/main.py <target> auto
```

### 📚 Documentation

- Complete README with examples
- Comprehensive command reference
- Installation and setup guide
- Troubleshooting section

### 🏆 What's New in v1.0

This release represents a complete transformation into a modern, enterprise-ready printer penetration testing toolkit with:

1. **Automatic Language Detection**: No more guessing which printer language to use
2. **HTTP Fallback**: Works with web-based printers when port 9100 is blocked
3. **Smart Connection Management**: Automatically tries multiple connection methods
4. **Enhanced Error Handling**: Robust retry logic and better error messages
5. **Structured Logging**: Advanced debugging capabilities
6. **OSINT Integration**: Built-in reconnaissance features
7. **CVE Lookup**: Automatic vulnerability database queries
8. **MIT License**: More permissive licensing for commercial use

### 🎯 Next Steps

1. Go to GitHub: https://github.com/mrhenrike/PrinterReaper
2. Click "Releases" → "Create a new release"
3. Select tag: v1.0
4. Release title: "PrinterReaper v1.0 - Advanced Printer Penetration Testing Toolkit"
5. Copy the content above as release notes
6. Click "Publish release"

This release marks the beginning of PrinterReaper as a standalone, enterprise-ready printer penetration testing toolkit!
