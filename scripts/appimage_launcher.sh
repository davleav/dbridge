#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
APPDIR=$(dirname $(dirname "$HERE"))

# Debug information
echo "Starting launcher script..."
echo "AppDir location: ${APPDIR}"

# Python paths
export PYTHONPATH="${APPDIR}/usr/lib/python3.10/site-packages:${APPDIR}/usr/lib/python3.10:${APPDIR}/usr/lib/python3.10/site-packages:${APPDIR}/usr/lib/python3.10:${PYTHONPATH}"
export PYTHONHOME="${APPDIR}/usr"

# Debug Python paths
echo "Python path configuration:"
echo "  PYTHONHOME = '${PYTHONHOME}'"
echo "  PYTHONPATH = '${PYTHONPATH}'"

# Library paths - make sure our libraries are found first
export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${LD_LIBRARY_PATH}"

# Debug: List available libraries
echo "Available Python libraries in AppDir:"
ls -la ${APPDIR}/usr/lib/libpython* 2>/dev/null || echo "No Python libraries found!"

# Qt paths - try both PyQt6 location and standard location
export QT_PLUGIN_PATH="${APPDIR}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins:${APPDIR}/usr/plugins:${QT_PLUGIN_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${APPDIR}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins/platforms:${APPDIR}/usr/plugins/platforms:${QT_QPA_PLATFORM_PLUGIN_PATH}"

# Additional Qt environment variables
export QT_DEBUG_PLUGINS=1
export QT_XCB_GL_INTEGRATION=xcb_glx
export XDG_DATA_DIRS="${APPDIR}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Run the PyInstaller binary directly
if [ -f "${APPDIR}/dbridge" ]; then
  exec "${APPDIR}/dbridge" "$@"
else
  echo "Error: dbridge binary not found at ${APPDIR}/dbridge"
  exit 1
fi