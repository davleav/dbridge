# GitHub Actions for DBridge

This document explains how to use GitHub Actions to build and release DBridge.

## Available Workflows

### 1. Build AppImage (Simple)

This workflow uses the `build_appimage_simple.sh` script to build an AppImage for Linux. It's designed to be more reliable by leveraging the script that works locally.

**File:** `.github/workflows/build-appimage-simple.yml`

**Triggers:**
- Push of a tag starting with 'v' (e.g., v0.8.1)
- Manual trigger from the GitHub Actions UI

**What it does:**
1. Sets up the build environment
2. Installs dependencies
3. Modifies the `build_appimage_simple.sh` script to work in GitHub Actions
4. Builds the AppImage
5. Uploads the AppImage as an artifact
6. Creates a release (if triggered by a tag or manually)

### 2. Original Build and Release Workflow

The original workflow for building and releasing the AppImage.

**File:** `.github/workflows/build-and-release.yml`

## How to Use

### Running a Workflow Manually

1. Go to the "Actions" tab in your GitHub repository
2. Select the workflow you want to run (e.g., "Build AppImage (Simple)")
3. Click the "Run workflow" button
4. Select the branch you want to run the workflow on
5. Click "Run workflow"

### Creating a Release with a Tag

To create a release with a specific version:

1. Create and push a tag with the version number:
   ```
   git tag v0.8.1
   git push origin v0.8.1
   ```

2. The workflow will automatically run and create a release with the AppImage attached.

## Troubleshooting

### Common Issues

1. **AppImage not found**
   - The workflow includes extensive search logic to find the AppImage in various locations
   - Check the workflow logs to see where it's looking and what it finds

2. **Build directory issues**
   - The workflow uses `/tmp/dbridge_build_tmp` as the build directory to avoid conflicts
   - It modifies the copy command to avoid recursive copying issues

3. **Missing dependencies**
   - The workflow installs all necessary dependencies for building the AppImage
   - If you need additional dependencies, add them to the "Install system dependencies" step

### Debugging

If you encounter issues:

1. Check the workflow logs for error messages
2. Look for the "Searching for any AppImage files" step to see if the AppImage was created but not found
3. Examine the "Current directory contents" output if the AppImage wasn't found

## Customizing the Workflow

If you need to customize the workflow:

1. Edit the `.github/workflows/build-appimage-simple.yml` file
2. Modify the "Modify build_appimage_simple.sh for GitHub Actions" step to make additional changes to the script
3. Add or modify steps as needed

## Comparing with Local Builds

The GitHub Actions workflow is designed to mimic your local build process as closely as possible. The main differences are:

1. It uses a different build directory (`/tmp/dbridge_build_tmp` instead of `$HOME/dbridge_build_tmp`)
2. It removes the interactive prompt for root user (not needed in GitHub Actions)
3. It has additional logic to find and handle the AppImage file

If your local build process changes, you may need to update the GitHub Actions workflow to match.