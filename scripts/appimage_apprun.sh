#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Debug information
echo "Starting AppRun script..."
echo "AppDir location: ${HERE}"

# Python paths
export PYTHONPATH="${HERE}/usr/lib/python3.10/site-packages:${HERE}/usr/lib/python3.10:${PYTHONPATH}"
export PYTHONHOME="${HERE}/usr"

# Library paths - make sure our libraries are found first
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Debug: List available libraries
echo "Available Python libraries in AppDir:"
ls -la ${HERE}/usr/lib/libpython* 2>/dev/null || echo "No Python libraries found!"

# Qt paths - try both PyQt6 location and standard location
export QT_PLUGIN_PATH="${HERE}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins:${HERE}/usr/plugins:${QT_PLUGIN_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins/platforms:${HERE}/usr/plugins/platforms:${QT_QPA_PLATFORM_PLUGIN_PATH}"

# Additional Qt environment variables
export QT_DEBUG_PLUGINS=1
export QT_XCB_GL_INTEGRATION=xcb_glx
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Execute the application with proper Python path
if [ -f "${HERE}/usr/bin/python3" ]; then
  export PYTHON="${HERE}/usr/bin/python3"
elif [ -f "${HERE}/usr/bin/python" ]; then
  export PYTHON="${HERE}/usr/bin/python"
else
  # Try to find Python in PATH
  PYTHON_PATH=$(which python3 2>/dev/null || which python 2>/dev/null)
  if [ -n "$PYTHON_PATH" ]; then
    export PYTHON="$PYTHON_PATH"
  else
    echo "Error: Python executable not found"
    exit 1
  fi
fi

# Execute the application
exec "${HERE}/usr/bin/dbridge" "$@"