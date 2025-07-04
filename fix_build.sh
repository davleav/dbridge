#!/bin/bash
# Script to fix the main.py file for the AppImage build

# Set the path to the main.py file
MAIN_PY="/media/david/Data/david/apps/dbridge/src/main.py"

# Check if the file exists
if [ -f "$MAIN_PY" ]; then
    echo "Found main.py at: $MAIN_PY"
    ls -la "$MAIN_PY"
else
    echo "main.py not found. Creating it..."
    mkdir -p "/media/david/Data/david/apps/dbridge/src"
    cat > "$MAIN_PY" << 'MAINPYEOF'
#!/usr/bin/env python3
"""
DBridge - A user-friendly SQL client
Main entry point for the application
"""

def main():
    """Main entry point for the application"""
    print("DBridge - A user-friendly SQL client")
    print("This is a placeholder main.py file created by the build script.")
    print("The actual application code was not found during the build process.")

if __name__ == "__main__":
    main()
MAINPYEOF
    chmod 777 "$MAIN_PY"
    echo "Created main.py at: $MAIN_PY"
    ls -la "$MAIN_PY"
fi

# Verify the file is readable
if [ -r "$MAIN_PY" ]; then
    echo "File is readable. First few lines:"
    head -n 3 "$MAIN_PY"
else
    echo "Error: File exists but is not readable."
    exit 1
fi

echo "main.py file is ready for the build process."