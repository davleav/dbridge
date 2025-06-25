"""
Connection manager for handling database connections
"""

from typing import Dict, List, Union, Optional, Any, Tuple

import sqlalchemy
from sqlalchemy import create_engine, inspect, Engine
from sqlalchemy.engine import Connection
import pandas as pd
import json
import os
import pathlib
import subprocess
import tempfile
import re
import base64
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class DatabaseConnection:
    """Class representing a database connection"""
    
    params: Dict[str, Any]
    engine: Optional[Engine]
    inspector: Optional[Any]
    user_permissions: Dict[str, bool]
    connection_manager: Optional[Any] = None
    
    def __init__(self, connection_params: Dict[str, Any]):
        """Initialize the connection with the given parameters
        
        Args:
            connection_params: Dictionary containing connection parameters
        """
        self.params = connection_params
        self.engine = None
        self.inspector = None
        self.user_permissions = {
            'can_create_database': False,
            'can_drop_database': False,
            'is_admin': False
        }
        self._connect()
        self._check_permissions()
    
    def _connect(self) -> None:
        """Establish the database connection"""
        connection_string = self._build_connection_string()
        self.engine = create_engine(connection_string)
        self.inspector = inspect(self.engine)
        
    def _check_permissions(self):
        """Check the permissions of the current user"""
        try:
            # Default to restricted permissions
            self.user_permissions = {
                'can_create_database': False,
                'can_drop_database': False,
                'is_admin': False
            }
            
            # Only MySQL is supported for permission checking currently
            if self.params['type'] != 'MySQL':
                return
                
            # Query to check if user has CREATE DATABASE privilege
            grants_query = "SHOW GRANTS FOR CURRENT_USER()"
            result = self.execute_query(grants_query)
            
            if result is not None and not result.empty:
                grants_text = ' '.join(result.iloc[:, 0].tolist())
                
                # Check for global privileges
                if 'ALL PRIVILEGES ON *.*' in grants_text:
                    self.user_permissions['can_create_database'] = True
                    self.user_permissions['can_drop_database'] = True
                    self.user_permissions['is_admin'] = True
                elif 'CREATE ON *.*' in grants_text:
                    self.user_permissions['can_create_database'] = True
                
                # Check for specific CREATE DATABASE privilege
                if 'CREATE DATABASE' in grants_text or 'CREATE' in grants_text:
                    self.user_permissions['can_create_database'] = True
                    
                # Check for specific DROP privilege
                if 'DROP' in grants_text:
                    self.user_permissions['can_drop_database'] = True
                    
            print(f"User permissions: {self.user_permissions}")
        except Exception as e:
            print(f"Error checking permissions: {e}")
            # If we can't check permissions, default to restricted
    
    def _build_connection_string(self) -> str:
        """Build the SQLAlchemy connection string
        
        Returns:
            SQLAlchemy connection string
            
        Raises:
            ValueError: If the database type is not supported
        """
        import urllib.parse
        
        # URL-encode the username and password to handle special characters
        if 'user' in self.params:
            encoded_user = urllib.parse.quote_plus(self.params['user'])
        else:
            encoded_user = ''
            
        if 'password' in self.params:
            encoded_password = urllib.parse.quote_plus(self.params['password'])
        else:
            encoded_password = ''
            
        if self.params['type'] == 'MySQL':
            # Handle case where database name is not provided
            if 'database' in self.params and self.params['database'].strip():
                return f"mysql+pymysql://{encoded_user}:{encoded_password}@{self.params['host']}:{self.params['port']}/{self.params['database']}"
            else:
                return f"mysql+pymysql://{encoded_user}:{encoded_password}@{self.params['host']}:{self.params['port']}/"
        elif self.params['type'] == 'PostgreSQL':
            # Handle case where database name is not provided
            if 'database' in self.params and self.params['database'].strip():
                return f"postgresql+psycopg2://{encoded_user}:{encoded_password}@{self.params['host']}:{self.params['port']}/{self.params['database']}"
            else:
                return f"postgresql+psycopg2://{encoded_user}:{encoded_password}@{self.params['host']}:{self.params['port']}/"
        elif self.params['type'] == 'SQLite':
            return f"sqlite:///{self.params['database']}"
        else:
            raise ValueError(f"Unsupported database type: {self.params['type']}")
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute a SQL query and return the results as a DataFrame
        
        Args:
            query: SQL query string to execute
            
        Returns:
            DataFrame containing the query results
            
        Raises:
            ValueError: If database connection is not established
        """
        if self.engine is None:
            raise ValueError("Database connection is not established")
        return pd.read_sql(query, self.engine)
    
    def execute_non_query(self, query: str) -> int:
        """Execute a non-query SQL statement (INSERT, UPDATE, DELETE, etc.)
        
        Args:
            query: SQL statement to execute
            
        Returns:
            Number of rows affected
            
        Raises:
            ValueError: If database connection is not established
        """
        if self.engine is None:
            raise ValueError("Database connection is not established")
        with self.engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                result = connection.execute(sqlalchemy.text(query))
                # The transaction will be automatically committed when the block exits
                # if no exceptions are raised
            return result.rowcount
    
    def get_database_name(self):
        """Get the name of the connected database"""
        if 'database' in self.params and self.params['database'].strip():
            return self.params['database']
        else:
            return "(No database selected)"
            
    def can_create_database(self):
        """Check if the current user can create databases"""
        return self.user_permissions.get('can_create_database', False)
        
    def can_drop_database(self):
        """Check if the current user can drop databases"""
        return self.user_permissions.get('can_drop_database', False)
        
    def is_admin(self):
        """Check if the current user has admin privileges"""
        return self.user_permissions.get('is_admin', False)
    
    def is_system_database(self, database_name):
        """Check if the given database is a system database
        
        Args:
            database_name: Name of the database to check
            
        Returns:
            True if it's a system database, False otherwise
        """
        if not database_name:
            return False
            
        # Common system database names across different database systems
        system_databases = [
            'information_schema',  # MySQL, PostgreSQL
            'mysql',               # MySQL
            'performance_schema',  # MySQL
            'sys',                 # MySQL
            'pg_catalog',          # PostgreSQL
            'postgres',            # PostgreSQL default admin database
            'template0',           # PostgreSQL
            'template1'            # PostgreSQL
        ]
        
        # Case-insensitive check
        return database_name.lower() in [db.lower() for db in system_databases]
    
    def get_available_databases(self):
        """Get a list of available databases on the server"""
        try:
            if self.engine is None:
                return []
                
            if self.params['type'] == 'MySQL':
                # For MySQL, use SHOW DATABASES query
                result = pd.read_sql("SHOW DATABASES", self.engine.connect())
                return result['Database'].tolist()
            elif self.params['type'] == 'PostgreSQL':
                # For PostgreSQL, query the pg_database system catalog
                result = pd.read_sql(
                    "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname",
                    self.engine.connect()
                )
                return result['datname'].tolist()
            elif self.params['type'] == 'SQLite':
                # SQLite doesn't have multiple databases in the same way
                return []
            else:
                return []
        except Exception as e:
            print(f"Error getting available databases: {e}")
            return []
    
    def use_database(self, database_name):
        """Switch to a different database"""
        if not database_name or database_name == self.get_database_name():
            return False
            
        try:
            # Update the database name in the connection parameters
            self.params['database'] = database_name
            
            # Reconnect with the new database
            self._connect()
            
            # Update the connection parameters in the connection manager if available
            # This is to ensure the connection parameters are saved with the new database
            if hasattr(self, 'connection_manager') and self.connection_manager:
                connection_name = self.params['name']
                if connection_name in self.connection_manager.connection_params:
                    self.connection_manager.connection_params[connection_name]['database'] = database_name
                    self.connection_manager.save_connections()
            
            return True
        except Exception as e:
            print(f"Error switching to database {database_name}: {e}")
            return False
    
    def deselect_database(self):
        """Deselect the current database and return to the no-database state"""
        # Check if we already have no database selected
        if self.get_database_name() == "(No database selected)":
            return False
            
        try:
            # Remove the database from the connection parameters
            if 'database' in self.params:
                del self.params['database']
            
            # Reconnect without a specific database
            self._connect()
            
            # Update the connection parameters in the connection manager if available
            if hasattr(self, 'connection_manager') and self.connection_manager:
                connection_name = self.params['name']
                if connection_name in self.connection_manager.connection_params:
                    if 'database' in self.connection_manager.connection_params[connection_name]:
                        del self.connection_manager.connection_params[connection_name]['database']
                    self.connection_manager.save_connections()
            
            return True
        except Exception as e:
            print(f"Error deselecting database: {e}")
            return False
    
    def get_tables(self):
        """Get a list of tables in the database"""
        try:
            if self.engine is None:
                return []
            # Refresh the inspector to ensure we get the latest table list
            self.inspector = inspect(self.engine)
            if self.inspector is None:
                return []
            return self.inspector.get_table_names()
        except Exception as e:
            # Log the error but return an empty list to avoid crashing
            print(f"Error getting tables: {e}")
            return []
    
    def get_views(self):
        """Get a list of views in the database"""
        try:
            if self.engine is None:
                return []
            # Refresh the inspector to ensure we get the latest view list
            self.inspector = inspect(self.engine)
            if self.inspector is None:
                return []
            return self.inspector.get_view_names()
        except Exception as e:
            # Some database drivers might not support views
            print(f"Error getting views: {e}")
            return []
    
    def get_columns(self, table_name):
        """Get the columns of a table"""
        try:
            if self.engine is None:
                raise ValueError("Database connection is not established")
            # Refresh the inspector to ensure we get the latest column information
            self.inspector = inspect(self.engine)
            if self.inspector is None:
                raise ValueError("Database inspector could not be created")
            columns = self.inspector.get_columns(table_name)
            return [{'name': col['name'], 'type': str(col['type'])} for col in columns]
        except Exception as e:
            print(f"Error getting columns for table '{table_name}': {e}")
            # Re-raise the exception to be handled by the caller
            raise
    
    def get_primary_key(self, table_name):
        """Get the primary key columns of a table"""
        if self.engine is None:
            return []
        # Refresh the inspector to ensure we get the latest primary key information
        self.inspector = inspect(self.engine)
        if self.inspector is None:
            return []
        return self.inspector.get_primary_keys(table_name)
    
    def get_foreign_keys(self, table_name):
        """Get the foreign keys of a table"""
        if self.engine is None:
            return []
        # Refresh the inspector to ensure we get the latest foreign key information
        self.inspector = inspect(self.engine)
        if self.inspector is None:
            return []
        return self.inspector.get_foreign_keys(table_name)
    
    def get_indexes(self, table_name):
        """Get the indexes of a table"""
        if self.engine is None:
            return []
        # Refresh the inspector to ensure we get the latest index information
        self.inspector = inspect(self.engine)
        if self.inspector is None:
            return []
        indexes = self.inspector.get_indexes(table_name)
        return [{'name': idx['name'], 'columns': idx['column_names']} for idx in indexes]
    
    def close(self):
        """Close the database connection"""
        if self.engine:
            self.engine.dispose()
    
    def export_database_to_sql(self, file_path, tables=None):
        """
        Export the entire database or specific tables to a SQL file
        
        Args:
            file_path (str): Path to save the SQL file
            tables (list, optional): List of table names to export. If None, export all tables.
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            db_type = self.params['type']
            
            if db_type == 'SQLite':
                return self._export_sqlite_to_sql(file_path, tables)
            elif db_type == 'MySQL':
                return self._export_mysql_to_sql(file_path, tables)
            elif db_type == 'PostgreSQL':
                return self._export_postgresql_to_sql(file_path, tables)
            else:
                raise ValueError(f"Export not supported for database type: {db_type}")
        except Exception as e:
            print(f"Export error: {e}")
            raise
    
    def _export_sqlite_to_sql(self, file_path, tables=None):
        """Export SQLite database to SQL file"""
        try:
            db_path = self.params['database']
            
            with open(file_path, 'w') as f:
                # Add header
                f.write(f"-- SQLite database export from DBridge\n")
                f.write(f"-- Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {os.path.basename(db_path)}\n\n")
                
                # Get list of tables to export
                if tables is None:
                    tables = self.get_tables()
                
                # Export each table
                for table in tables:
                    # Get table schema
                    schema_query = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';"
                    schema_result = self.execute_query(schema_query)
                    
                    if not schema_result.empty:
                        create_table_sql = schema_result.iloc[0, 0]
                        f.write(f"{create_table_sql};\n\n")
                    
                    # Get table data
                    data_query = f"SELECT * FROM {table};"
                    data = self.execute_query(data_query)
                    
                    if not data.empty:
                        f.write(f"-- Data for table {table}\n")
                        
                        # Generate INSERT statements
                        for _, row in data.iterrows():
                            values = []
                            for val in row:
                                if pd.isna(val):
                                    values.append("NULL")
                                elif isinstance(val, (int, float)):
                                    values.append(str(val))
                                else:
                                    # Escape single quotes in string values
                                    val_str = str(val).replace("'", "''")
                                    values.append(f"'{val_str}'")
                            
                            f.write(f"INSERT INTO {table} VALUES ({', '.join(values)});\n")
                        
                        f.write("\n")
            
            return True
        except Exception as e:
            print(f"SQLite export error: {e}")
            raise
    
    def _export_mysql_to_sql(self, file_path, tables=None):
        """Export MySQL database to SQL file using mysqldump"""
        try:
            # Check if mysqldump is available
            try:
                subprocess.run(['mysqldump', '--version'], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                raise RuntimeError("mysqldump utility not found. Please install MySQL client tools.")
            
            # Build mysqldump command
            cmd = [
                'mysqldump',
                '--host=' + self.params['host'],
                '--port=' + str(self.params['port']),
                '--user=' + self.params['user'],
                '--add-drop-table',
                '--skip-lock-tables'
            ]
            
            # Add password if provided
            if 'password' in self.params and self.params['password']:
                # Use MYSQL_PWD environment variable instead of --password option
                # This avoids password being visible in process list
                env = os.environ.copy()
                env['MYSQL_PWD'] = self.params['password']
            else:
                env = os.environ.copy()
            
            # Handle database and tables
            if tables:
                # For specific tables, just specify the database and table names
                cmd.append(self.params['database'])
                cmd.extend(tables)
            else:
                # For entire database, use --databases option
                cmd.append('--databases')
                cmd.append(self.params['database'])
            
            # Run mysqldump and save output to file
            with open(file_path, 'w') as f:
                subprocess.run(cmd, stdout=f, env=env, check=True)
            
            return True
        except Exception as e:
            print(f"MySQL export error: {e}")
            raise
    
    def _export_postgresql_to_sql(self, file_path, tables=None):
        """Export PostgreSQL database to SQL file using pg_dump"""
        try:
            # Check if pg_dump is available
            try:
                subprocess.run(['pg_dump', '--version'], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                raise RuntimeError("pg_dump utility not found. Please install PostgreSQL client tools.")
            
            # Create a temporary password file for pg_dump
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
                temp.write(self.params.get('password', ''))
                temp_path = temp.name
            
            try:
                # Set environment variables for PostgreSQL connection
                env = os.environ.copy()
                env['PGPASSFILE'] = temp_path
                
                # Build pg_dump command
                cmd = [
                    'pg_dump',
                    '--host=' + self.params['host'],
                    '--port=' + str(self.params['port']),
                    '--username=' + self.params['user'],
                    '--dbname=' + self.params['database'],
                    '--no-password',  # Use password file instead
                    '--clean'  # Add DROP statements
                ]
                
                # Add specific tables if provided
                if tables:
                    for table in tables:
                        cmd.extend(['--table', table])
                
                # Run pg_dump and save output to file
                with open(file_path, 'w') as f:
                    subprocess.run(cmd, stdout=f, env=env, check=True)
                
                return True
            finally:
                # Clean up the temporary password file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            print(f"PostgreSQL export error: {e}")
            raise
    
    def import_sql_file(self, file_path):
        """
        Import a SQL file into the database
        
        Args:
            file_path (str): Path to the SQL file to import
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            db_type = self.params['type']
            
            if db_type == 'SQLite':
                return self._import_sql_to_sqlite(file_path)
            elif db_type == 'MySQL':
                return self._import_sql_to_mysql(file_path)
            elif db_type == 'PostgreSQL':
                return self._import_sql_to_postgresql(file_path)
            else:
                raise ValueError(f"Import not supported for database type: {db_type}")
        except Exception as e:
            print(f"Import error: {e}")
            raise
    
    def _import_sql_to_sqlite(self, file_path):
        """Import SQL file to SQLite database"""
        try:
            # Read the SQL file
            with open(file_path, 'r') as f:
                sql_script = f.read()
            
            # Split the script into individual statements
            # This is a simple approach and might not work for all SQL files
            statements = re.split(r';\s*\n', sql_script)
            
            # Execute each statement
            if self.engine is None:
                raise ValueError("Database connection is not established")
                
            with self.engine.begin() as connection:
                for statement in statements:
                    if statement.strip():
                        connection.execute(sqlalchemy.text(statement))
            
            return True
        except Exception as e:
            print(f"SQLite import error: {e}")
            raise
    
    def _import_sql_to_mysql(self, file_path):
        """Import SQL file to MySQL database using mysql client"""
        try:
            # Check if mysql client is available
            try:
                subprocess.run(['mysql', '--version'], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                raise RuntimeError("mysql client utility not found. Please install MySQL client tools.")
            
            # Build mysql command
            cmd = [
                'mysql',
                '--host=' + self.params['host'],
                '--port=' + str(self.params['port']),
                '--user=' + self.params['user'],
                '--database=' + self.params['database']
            ]
            
            # Set up environment with password if provided
            if 'password' in self.params and self.params['password']:
                # Use MYSQL_PWD environment variable instead of --password option
                # This avoids password being visible in process list
                env = os.environ.copy()
                env['MYSQL_PWD'] = self.params['password']
            else:
                env = os.environ.copy()
            
            # Run mysql client with input from file
            with open(file_path, 'r') as f:
                subprocess.run(cmd, stdin=f, env=env, check=True)
            
            return True
        except Exception as e:
            print(f"MySQL import error: {e}")
            raise
    
    def _import_sql_to_postgresql(self, file_path):
        """Import SQL file to PostgreSQL database using psql"""
        try:
            # Check if psql is available
            try:
                subprocess.run(['psql', '--version'], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                raise RuntimeError("psql utility not found. Please install PostgreSQL client tools.")
            
            # Create a temporary password file for psql
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
                temp.write(self.params.get('password', ''))
                temp_path = temp.name
            
            try:
                # Set environment variables for PostgreSQL connection
                env = os.environ.copy()
                env['PGPASSFILE'] = temp_path
                
                # Build psql command
                cmd = [
                    'psql',
                    '--host=' + self.params['host'],
                    '--port=' + str(self.params['port']),
                    '--username=' + self.params['user'],
                    '--dbname=' + self.params['database'],
                    '--no-password',  # Use password file instead
                    '--file=' + file_path
                ]
                
                # Run psql
                subprocess.run(cmd, env=env, check=True)
                
                return True
            finally:
                # Clean up the temporary password file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            print(f"PostgreSQL import error: {e}")
            raise


class ConnectionManager:
    """Manager for database connections"""
    
    def __init__(self):
        """Initialize the connection manager"""
        self.connections = {}  # Active connections
        self.connection_params = {}  # Stored connection parameters
        self.config_dir = self._get_config_dir()
        self._setup_encryption()
        self.load_connections()
    
    def _get_config_dir(self):
        """Get the configuration directory for the application"""
        home = pathlib.Path.home()
        config_dir = home / ".config" / "dbridge"
        
        # Create the directory if it doesn't exist
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
        
        return config_dir
        
    def _setup_encryption(self):
        """Set up encryption for password storage"""
        # Path to the encryption key file
        self.key_file = self.config_dir / "encryption.key"
        
        # Generate or load encryption key
        if not self.key_file.exists():
            # Generate a new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set permissions to restrict access
            os.chmod(self.key_file, 0o600)
        else:
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
                
        # Create Fernet cipher
        self.cipher = Fernet(key)
    
    def encrypt_password(self, password):
        """Encrypt a password for storage"""
        if not password:
            return None
        return self.cipher.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password):
        """Decrypt a stored password"""
        if not encrypted_password:
            return ""
        try:
            return self.cipher.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            print(f"Error decrypting password: {e}")
            return ""
    
    def create_connection(self, connection_params):
        """Create a new database connection"""
        connection = DatabaseConnection(connection_params)
        
        # Set a reference to the connection manager in the connection object
        # This allows the connection to update its parameters in the manager
        if connection is not None:
            connection.connection_manager = self
        
        name = connection_params['name']
        self.connections[name] = connection
        self.connection_params[name] = connection_params.copy()
        
        # Save the updated connections
        self.save_connections()
        
        return connection
    
    def get_connection(self, name):
        """Get a connection by name"""
        # If connection is already active, return it
        if name in self.connections:
            connection = self.connections.get(name)
            # Ensure the connection has a reference to the connection manager
            if connection is not None and not hasattr(connection, 'connection_manager'):
                connection.connection_manager = self
            return connection
        
        # If connection is not active but we have its parameters, reconnect
        if name in self.connection_params:
            # Create a copy of the parameters to avoid modifying the stored ones
            params = self.connection_params[name].copy()
            return self.create_connection(params)
        
        return None
    
    def get_connection_names(self):
        """Get a list of all connection names (active and stored)"""
        return list(self.connection_params.keys())
    
    def is_connected(self, name):
        """Check if a connection is currently active"""
        return name in self.connections
    
    def close_connection(self, name):
        """Close a connection by name but keep its parameters"""
        if name in self.connections:
            self.connections[name].close()
            # Remove the connection from the dictionary
            del self.connections[name]
            # Note: We keep the connection_params entry for reconnecting later
    
    def remove_connection(self, name):
        """Completely remove a connection and its parameters"""
        self.close_connection(name)
        if name in self.connection_params:
            del self.connection_params[name]
            # Save the updated connections
            self.save_connections()
    
    def close_all(self):
        """Close all connections but keep their parameters"""
        for connection in list(self.connections.values()):
            connection.close()
        self.connections.clear()
        # Note: We keep the connection_params entries for reconnecting later
    
    def save_connections(self):
        """Save connection parameters to a file"""
        connections_file = self.config_dir / "connections.json"
        
        # Create a copy of connection parameters with encrypted passwords if save_password is True
        secure_params = {}
        for name, params in self.connection_params.items():
            secure_params[name] = params.copy()
            
            # Handle password based on save_password flag
            if 'password' in secure_params[name]:
                if params.get('save_password', False) and params['password']:
                    # Encrypt the password for storage
                    secure_params[name]['encrypted_password'] = self.encrypt_password(params['password'])
                # Always remove the plaintext password
                secure_params[name]['password'] = ''
        
        try:
            with open(connections_file, 'w') as f:
                json.dump(secure_params, f, indent=2)
        except Exception as e:
            print(f"Error saving connections: {e}")
    
    def load_connections(self):
        """Load connection parameters from a file"""
        connections_file = self.config_dir / "connections.json"
        
        if not connections_file.exists():
            return
        
        try:
            with open(connections_file, 'r') as f:
                loaded_params = json.load(f)
            
            # Process loaded parameters
            for name, params in loaded_params.items():
                # Decrypt password if encrypted_password exists
                if 'encrypted_password' in params:
                    params['password'] = self.decrypt_password(params['encrypted_password'])
                    params['save_password'] = True
                
            # Update our connection parameters
            self.connection_params.update(loaded_params)
        except Exception as e:
            print(f"Error loading connections: {e}")