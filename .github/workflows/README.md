# GitHub Actions Workflows

This directory contains GitHub Actions workflows for building and releasing DBridge.

## Available Workflows

### 1. Build and Release AppImage (Original)
- **File:** `build-and-release.yml`
- **Description:** The original workflow for building and releasing the AppImage.

### 2. Build AppImage (Simple)
- **File:** `build-appimage-simple.yml`
- **Description:** A simplified workflow that uses the `build_appimage_simple.sh` script to build the AppImage.
- **Advantages:** Uses the same script that works locally, which may be more reliable.

### 3. Build macOS
- **File:** `build-macos.yml`
- **Description:** Workflow for building the macOS version.

### 4. Build Windows
- **File:** `build-windows.yml`
- **Description:** Workflow for building the Windows version.

## How to Use

### Running a Workflow Manually

1. Go to the "Actions" tab in your GitHub repository
2. Select the workflow you want to run
3. Click the "Run workflow" button
4. Select the branch you want to run the workflow on
5. Click "Run workflow"

### Creating a Release

To create a release:

1. Create and push a tag with the version number:
   ```
   git tag v0.8.1
   git push origin v0.8.1
   ```

2. The workflow will automatically run and create a release with the AppImage attached.

## Troubleshooting

If you encounter issues with the original `build-and-release.yml` workflow, try using the simplified `build-appimage-simple.yml` workflow instead, which uses the same script that works locally.