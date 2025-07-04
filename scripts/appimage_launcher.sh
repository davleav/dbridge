#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
APPDIR=$(dirname $(dirname "$HERE"))

# Python paths
export PYTHONPATH="${APPDIR}/usr/lib/python3.10/site-packages:${APPDIR}/usr/lib/python3.10:${PYTHONPATH}"
export PYTHONHOME="${APPDIR}/usr"

# Library paths
export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${LD_LIBRARY_PATH}"

# Qt paths - try both PyQt6 location and standard location
export QT_PLUGIN_PATH="${APPDIR}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins:${APPDIR}/usr/plugins:${QT_PLUGIN_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${APPDIR}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins/platforms:${APPDIR}/usr/plugins/platforms:${QT_QPA_PLATFORM_PLUGIN_PATH}"

# Additional Qt environment variables
export QT_DEBUG_PLUGINS=1
export QT_XCB_GL_INTEGRATION=xcb_glx
export XDG_DATA_DIRS="${APPDIR}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Change to the Python package directory and run the main module
cd "${APPDIR}/usr/lib/python3.10/site-packages"
# Use absolute path to Python if available, otherwise try to find it
if [ -f "${APPDIR}/usr/bin/python3" ]; then
  "${APPDIR}/usr/bin/python3" -m src.main
elif [ -f "${APPDIR}/usr/bin/python" ]; then
  "${APPDIR}/usr/bin/python" -m src.main
else
  # Try to find Python in PATH
  PYTHON_PATH=$(which python3 2>/dev/null || which python 2>/dev/null)
  if [ -n "$PYTHON_PATH" ]; then
    "$PYTHON_PATH" -m src.main
  else
    echo "Error: Python executable not found"
    exit 1
  fi
fi