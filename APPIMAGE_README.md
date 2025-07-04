# DBridge AppImage Instructions

This document provides instructions for running the DBridge AppImage.

## Prerequisites

The DBridge AppImage requires the following dependencies:

- `libxcb-cursor.so.0` (part of the `libxcb-cursor0` package on Debian/Ubuntu)

## Installation

1. Make the AppImage executable:
   ```
   chmod +x DBridge-Beta-0.8.0-x86_64.AppImage
   ```

2. Install dependencies (if needed):
   ```
   ./install_deps.sh
   ```

## Running DBridge

After installing dependencies, you can run DBridge by executing the AppImage:

```
./DBridge-Beta-0.8.0-x86_64.AppImage
```

## Troubleshooting

If you encounter the error message about missing `libxcb-cursor.so.0`:

```
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
```

Run the `install_deps.sh` script to install the required dependencies:

```
./install_deps.sh
```

If the script doesn't work for your distribution, you'll need to install the package manually:

- Debian/Ubuntu: `sudo apt-get install libxcb-cursor0`
- Fedora: `sudo dnf install libxcb-cursor`
- CentOS/RHEL: `sudo yum install libxcb-cursor`
- Arch Linux: `sudo pacman -S libxcb`

## Alternative Platforms

If you still have issues with the XCB platform, you can try forcing DBridge to use a different Qt platform:

```
QT_QPA_PLATFORM=wayland ./DBridge-Beta-0.8.0-x86_64.AppImage
```

Other platform options include:
- `wayland-egl`
- `eglfs`
- `minimal`