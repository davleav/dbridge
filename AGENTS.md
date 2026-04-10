# Repository Guidelines

## Project Structure & Module Organization
- `src/`: Core application logic and UI components.
    - `core/`: Core logic for database connection management (`connection_manager.py`).
    - `ui/`: PyQt6-based user interface components. `main_window.py` is the primary UI container, while `database_manager.py` handles UI-to-database interaction logic.
- `tests/`: Extensive test suite for both core and UI components, mirroring the `src/` directory structure.
- `scripts/`: Helper scripts for AppImage packaging and icon conversion.
- Root: Contains configuration files (`requirements.txt`, `setup.py`, `pytest.ini`) and platform-specific build scripts (`build_appimage.sh`, `build_macos.sh`, `build_windows.bat`).

## Build, Test, and Development Commands
- **Install dependencies**: `pip install -r requirements.txt`
- **Run application**: `python -m src.main`
- **Run all tests**: `./run_tests.py` or `pytest`
- **Run specific tests**: `./run_tests.py [module_name]` (e.g., `./run_tests.py connection_manager`)
- **Run with coverage**: `coverage run run_tests.py && coverage report -m`
- **Build AppImage**: `bash build_appimage.sh`
- **Build Windows**: `pyinstaller dbridge_windows.spec`

## Coding Style & Naming Conventions
- Python 3.8+ using PyQt6 for UI and SQLAlchemy for database interaction.
- UI components are decoupled from core database logic via `DatabaseManager`.
- Standard Python naming conventions are followed (lowercase with underscores for functions/variables, PascalCase for classes).

## Testing Guidelines
- Tests are located in the `tests/` directory.
- **Prefer `run_tests.py`** as it mocks blocking PyQt6 dialogs (`QMessageBox`, `QFileDialog`, `QInputDialog`) to ensure headless test execution doesn't hang.
- UI tests heavily utilize mocks to simulate user interactions without requiring an active display.

## Commit & Pull Request Guidelines
- Commit messages should be descriptive and typically start with a verb (e.g., `fix issue...`, `add feature...`, `improve handling...`).
- CI/CD builds for AppImage are triggered by version tags (e.g., `v0.9.0`).
