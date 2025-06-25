# DBridge (Beta 0.8.1)

> **Note:** This is a beta version (0.8.1) of DBridge. Some features may be incomplete or subject to change.

A user-friendly SQL client for Linux that runs as an AppImage.

## Features

- Clean, intuitive user interface
- Connect to MySQL, PostgreSQL, and SQLite databases
- Tabbed interface for working with multiple database connections simultaneously
- SQL query editor with syntax highlighting
- Advanced hierarchical database structure browser with ability to:
  - View and select from available databases on the server
  - Easily switch between databases or deselect the current database
  - Browse tables, views, columns, indexes and their structure
  - Manage any database object you have permission to access, regardless of which database is currently selected
  - Permission-aware interface that adapts to user access rights
- Query results viewer with export capabilities (CSV, Excel)
- Detailed row view with customizable layout for examining individual records
  - Double-click on any row to view detailed information
  - Resize data fields to focus on important information
  - Toggle between raw and rendered views for HTML and Markdown content
- Import and export databases or individual tables (SQL, CSV, Excel)
- Customizable interface with show/hide options for toolbar and database browser
- Multiple themes (light and dark) for comfortable viewing in any environment
- Packaged as an AppImage for easy installation

## Installation

### Using the AppImage

1. Download the latest `DBridge-Beta-0.8.1-x86_64.AppImage` from the releases page
2. Make it executable: `chmod +x DBridge-Beta-0.8.1-x86_64.AppImage`
3. Run it: `./DBridge-Beta-0.8.1-x86_64.AppImage`

### Building from Source

1. Clone this repository:
   ```
   git clone https://github.com/davleav/dbridge.git
   cd dbridge
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python -m src.main
   ```

4. (Optional) Build an AppImage:
   ```
   bash build_appimage.sh
   ```
   This will create a `DBridge-Beta-0.8.1-x86_64.AppImage` file.

## Usage

### Connecting to a Database

1. Click on the "Connect" button in the toolbar or select "File > New Connection"
2. Select your database type (MySQL, PostgreSQL, or SQLite)
3. Enter the connection details
4. Click "Test Connection" to verify the connection works
5. Click "OK" to connect
6. A new tab will be created for your database connection

#### Working with Multiple Connections

- Each connection opens in its own tab
- Switch between connections by clicking on the tabs
- Close a connection by clicking the "x" on the tab
- Open previously saved connections from the "File > Saved Connections" menu
- You can have multiple database connections open simultaneously

### Running Queries

1. Type your SQL query in the query editor
2. Press F5 or click the "Run Query" button to execute
3. View the results in the results tab

### Browsing Database Structure

1. Use the hierarchical database browser panel on the left to explore databases, tables, views, columns, indexes, and their structure
2. Double-click on a table to generate a SELECT query
3. Right-click on database objects for additional options
4. Expand/collapse tree nodes to navigate through the database hierarchy

#### Working with Available Databases

1. **Hierarchical Database Management**:
   - The browser displays a hierarchical tree of all databases you have access to
   - You can manage any database object regardless of which database is currently selected
   - The interface adapts to your permission level, showing only actions you're authorized to perform

2. **Viewing Available Databases**:
   - All accessible databases are shown in the hierarchical tree
   - This allows you to see and select from all databases you have access to

3. **Selecting a Database**:
   - Double-click on a database in the tree to select it
   - Alternatively, right-click on a database and select "Use Database '[database name]'"
   - The connection tab title will update to show the selected database

4. **Deselecting a Database**:
   - Right-click on the database root item and select "Deselect Database"
   - This will return to the "no database selected" state
   - Useful when you need to switch between databases or explore what databases are available

5. **Managing Database Objects**:
   - Expand a database node to see its tables, views, and other objects
   - Further expand table nodes to see columns, indexes, and other structural elements
   - Right-click on any object to see available actions based on your permissions

### Exporting Results

1. After running a query, click the "Export" button in the results toolbar
2. Choose a file format (CSV or Excel)
3. Select a location to save the file

### Using the Row Details Page

1. **Accessing Row Details**:
   - Double-click on any row in the query results to open the Row Details page
   - This provides a more detailed view of all fields in the selected record

2. **Customizing the View**:
   - Resize individual data fields by dragging the borders
   - Adjust the layout to focus on important information
   - The customized layout persists between sessions

3. **Working with Rich Content**:
   - For fields containing HTML or Markdown content:
     - Toggle between raw text view and rendered view
     - Use the view toggle button in the field header
     - Rendered view displays the formatted content as it would appear in a browser
     - Raw view shows the unprocessed HTML/Markdown code

### Importing and Exporting Databases

#### Exporting a Database or Table

1. **Export Entire Database**:
   - Right-click on the database name in the database browser
   - Select "Export Database..."
   - Choose export options (entire database or selected tables)
   - Select a file format (SQL, CSV, or Excel)
   - Choose a location to save the file

2. **Export a Single Table**:
   - Right-click on a table in the database browser
   - Select "Export" and choose a format (SQL, CSV, or Excel)
   - Choose a location to save the file

3. **From the Menu**:
   - Select "File > Import/Export > Export Database..."
   - Configure export options and proceed

#### Importing SQL Files

1. **Import into a Database**:
   - Right-click on the database name in the database browser
   - Select "Import SQL File..."
   - Select the SQL file to import
   - Confirm the import operation

2. **From the Menu**:
   - Select "File > Import/Export > Import SQL File..."
   - Select the SQL file to import
   - Confirm the import operation

### Customizing the Interface

1. **Show/Hide Main Toolbar**:
   - Select "Tools > Hide/Show Main Toolbar" from the menu
   - Alternatively, right-click on the menu bar or toolbar to toggle visibility

2. **Show/Hide Database Browser**:
   - Select "Tools > Hide/Show Database Browser" from the menu
   - This allows you to maximize space for the query editor and results

3. **Changing Application Theme**:
   - Select "Edit > Theme" from the menu
   - Choose from available themes:
     - Light Default: Standard light theme
     - Light Blue: Light theme with blue accents
     - Dark Default: Standard dark theme
     - Dark Blue: Dark theme with blue accents
   - The theme selection is saved and will be applied when you restart the application

## Testing

DBridge includes a comprehensive test suite to ensure functionality works as expected:

1. Run all tests:
   ```
   ./run_tests.py
   ```

2. Run specific test modules:
   ```
   python -m unittest tests.test_connection_manager
   ```

3. Run with coverage report:
   ```
   pip install coverage
   coverage run run_tests.py
   coverage report -m
   ```

## Requirements

- Python 3.8 or higher
- PyQt6
- SQLAlchemy
- Database drivers (pymysql, psycopg2, etc.)

## License

This project is licensed under the MIT License - see the LICENSE file for details.