"""
Tests for the database connection manager
"""

import unittest
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

import pandas as pd
from sqlalchemy import text

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.connection_manager import ConnectionManager, DatabaseConnection


class TestConnectionManager(unittest.TestCase):
    """Test cases for the ConnectionManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.connection_manager = ConnectionManager()
    
    def test_create_connection(self):
        """Test creating a connection"""
        # Create a temporary SQLite database for testing
        with tempfile.NamedTemporaryFile(suffix='.db') as temp_db:
            # Create a test table
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
            cursor.execute("INSERT INTO test VALUES (1, 'Test Name')")
            conn.commit()
            conn.close()
            
            # Create a connection using our ConnectionManager
            connection_params = {
                'name': 'test_connection',
                'type': 'SQLite',
                'database': temp_db.name
            }
            
            with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
                 patch('src.core.connection_manager.inspect') as mock_inspect:
                # Mock the SQLAlchemy engine
                mock_engine = MagicMock()
                mock_create_engine.return_value = mock_engine
                
                # Mock the inspector
                mock_inspector = MagicMock()
                mock_inspect.return_value = mock_inspector
                
                # Create the connection
                connection = self.connection_manager.create_connection(connection_params)
                
                # Check that the connection was created and stored
                self.assertIn('test_connection', self.connection_manager.connections)
                self.assertEqual(connection, self.connection_manager.connections['test_connection'])
                
                # Check that create_engine was called with the correct connection string
                mock_create_engine.assert_called_once_with(f"sqlite:///{temp_db.name}")
                
                # Check that the connection has a reference to the connection manager
                self.assertTrue(hasattr(connection, 'connection_manager'))
                self.assertEqual(connection.connection_manager, self.connection_manager)
    
    def test_get_connection(self):
        """Test getting a connection by name"""
        # Add a mock connection to the manager
        mock_connection = MagicMock()
        self.connection_manager.connections['test_connection'] = mock_connection
        
        # Get the connection
        connection = self.connection_manager.get_connection('test_connection')
        
        # Check that the correct connection was returned
        self.assertEqual(connection, mock_connection)
        
        # Check that the connection has a reference to the connection manager
        self.assertTrue(hasattr(mock_connection, 'connection_manager'))
        
        # Check that a non-existent connection returns None
        self.assertIsNone(self.connection_manager.get_connection('non_existent'))
    
    def test_get_connection_reconnect(self):
        """Test getting a connection that needs to be reconnected"""
        # Add connection parameters but no active connection
        test_params = {
            'name': 'test_reconnect',
            'type': 'SQLite',
            'database': ':memory:'
        }
        self.connection_manager.connection_params['test_reconnect'] = test_params
        
        # Mock create_connection to return a mock connection
        mock_connection = MagicMock()
        self.connection_manager.create_connection = MagicMock(return_value=mock_connection)
        
        # Get the connection
        connection = self.connection_manager.get_connection('test_reconnect')
        
        # Check that create_connection was called with the correct parameters
        self.connection_manager.create_connection.assert_called_once_with(test_params)
        
        # Check that the correct connection was returned
        self.assertEqual(connection, mock_connection)
    
    def test_get_connection_names(self):
        """Test getting all connection names"""
        # Add some connection parameters
        self.connection_manager.connection_params = {
            'connection1': {'name': 'connection1'},
            'connection2': {'name': 'connection2'},
            'connection3': {'name': 'connection3'}
        }
        
        # Get the connection names
        names = self.connection_manager.get_connection_names()
        
        # Check that all names were returned
        self.assertEqual(set(names), {'connection1', 'connection2', 'connection3'})
    
    def test_is_connected(self):
        """Test checking if a connection is active"""
        # Add a mock connection to the manager
        mock_connection = MagicMock()
        self.connection_manager.connections['active_connection'] = mock_connection
        
        # Add connection parameters for an inactive connection
        self.connection_manager.connection_params['inactive_connection'] = {'name': 'inactive_connection'}
        
        # Check active connection
        self.assertTrue(self.connection_manager.is_connected('active_connection'))
        
        # Check inactive connection
        self.assertFalse(self.connection_manager.is_connected('inactive_connection'))
        
        # Check non-existent connection
        self.assertFalse(self.connection_manager.is_connected('non_existent'))
    
    def test_close_connection(self):
        """Test closing a connection"""
        # Add a mock connection to the manager
        mock_connection = MagicMock()
        self.connection_manager.connections['test_connection'] = mock_connection
        self.connection_manager.connection_params['test_connection'] = {'name': 'test_connection'}
        
        # Close the connection
        self.connection_manager.close_connection('test_connection')
        
        # Check that the connection was closed and removed from active connections
        mock_connection.close.assert_called_once()
        self.assertNotIn('test_connection', self.connection_manager.connections)
        
        # Check that the connection parameters were kept
        self.assertIn('test_connection', self.connection_manager.connection_params)
    
    def test_remove_connection(self):
        """Test completely removing a connection"""
        # Add a mock connection to the manager
        mock_connection = MagicMock()
        self.connection_manager.connections['test_connection'] = mock_connection
        self.connection_manager.connection_params['test_connection'] = {'name': 'test_connection'}
        
        # Remove the connection
        self.connection_manager.remove_connection('test_connection')
        
        # Check that the connection was closed and removed from active connections
        mock_connection.close.assert_called_once()
        self.assertNotIn('test_connection', self.connection_manager.connections)
        
        # Check that the connection parameters were also removed
        self.assertNotIn('test_connection', self.connection_manager.connection_params)
    
    def test_close_all(self):
        """Test closing all connections"""
        # Clear any existing connections first
        self.connection_manager.connections.clear()
        self.connection_manager.connection_params.clear()
        
        # Add multiple mock connections to the manager
        mock_connection1 = MagicMock()
        mock_connection2 = MagicMock()
        self.connection_manager.connections['connection1'] = mock_connection1
        self.connection_manager.connections['connection2'] = mock_connection2
        self.connection_manager.connection_params['connection1'] = {'name': 'connection1'}
        self.connection_manager.connection_params['connection2'] = {'name': 'connection2'}
        
        # Close all connections
        self.connection_manager.close_all()
        
        # Check that all connections were closed and removed from active connections
        mock_connection1.close.assert_called_once()
        mock_connection2.close.assert_called_once()
        self.assertEqual(len(self.connection_manager.connections), 0)
        
        # Check that the connection parameters were kept
        self.assertEqual(len(self.connection_manager.connection_params), 2)
        self.assertIn('connection1', self.connection_manager.connection_params)
        self.assertIn('connection2', self.connection_manager.connection_params)


class TestDatabaseConnection(unittest.TestCase):
    """Test cases for the DatabaseConnection class"""
    
    def test_get_database_name(self):
        """Test getting the database name"""
        # Test with a database name provided
        connection_params_with_db = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        # Test without a database name
        connection_params_without_db = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass'
        }
        
        with patch('src.core.connection_manager.create_engine'), \
             patch('src.core.connection_manager.inspect'):
            
            # Test with database name
            connection_with_db = DatabaseConnection(connection_params_with_db)
            self.assertEqual(connection_with_db.get_database_name(), 'testdb')
            
            # Test without database name
            connection_without_db = DatabaseConnection(connection_params_without_db)
            self.assertEqual(connection_without_db.get_database_name(), "(No database selected)")
    
    def test_sqlite_connection_string(self):
        """Test building a SQLite connection string"""
        connection_params = {
            'name': 'test_sqlite',
            'type': 'SQLite',
            'database': '/path/to/database.db'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Check that create_engine was called with the correct connection string
            mock_create_engine.assert_called_once_with('sqlite:////path/to/database.db')
    
    def test_mysql_connection_string(self):
        """Test building a MySQL connection string"""
        connection_params = {
            'name': 'test_mysql',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Check that create_engine was called with the correct connection string
            mock_create_engine.assert_called_once_with(
                'mysql+pymysql://testuser:testpass@localhost:3306/testdb'
            )
            
    def test_mysql_connection_string_without_database(self):
        """Test building a MySQL connection string without a database name"""
        connection_params = {
            'name': 'test_mysql_no_db',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Check that create_engine was called with the correct connection string (without database)
            mock_create_engine.assert_called_once_with(
                'mysql+pymysql://testuser:testpass@localhost:3306/'
            )
    
    def test_postgresql_connection_string(self):
        """Test building a PostgreSQL connection string"""
        connection_params = {
            'name': 'test_postgresql',
            'type': 'PostgreSQL',
            'host': 'localhost',
            'port': 5432,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Check that create_engine was called with the correct connection string
            mock_create_engine.assert_called_once_with(
                'postgresql+psycopg2://testuser:testpass@localhost:5432/testdb'
            )
            
    def test_postgresql_connection_string_without_database(self):
        """Test building a PostgreSQL connection string without a database name"""
        connection_params = {
            'name': 'test_postgresql_no_db',
            'type': 'PostgreSQL',
            'host': 'localhost',
            'port': 5432,
            'user': 'testuser',
            'password': 'testpass'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Check that create_engine was called with the correct connection string (without database)
            mock_create_engine.assert_called_once_with(
                'postgresql+psycopg2://testuser:testpass@localhost:5432/'
            )
    
    def test_get_available_databases_mysql(self):
        """Test getting available databases for MySQL"""
        connection_params = {
            'name': 'test_mysql',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect, \
             patch('src.core.connection_manager.pd.read_sql') as mock_read_sql:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Mock read_sql to return a DataFrame with database names
            mock_df = pd.DataFrame({'Database': ['db1', 'db2', 'db3']})
            mock_read_sql.return_value = mock_df
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Get available databases
            databases = connection.get_available_databases()
            
            # Check that read_sql was called with the correct query for SHOW DATABASES
            # Note: We're checking the last call since _check_permissions also calls read_sql
            mock_read_sql.assert_called_with("SHOW DATABASES", mock_connection)
            
            # Check that the correct databases were returned
            self.assertEqual(databases, ['db1', 'db2', 'db3'])
    
    def test_get_available_databases_postgresql(self):
        """Test getting available databases for PostgreSQL"""
        connection_params = {
            'name': 'test_postgresql',
            'type': 'PostgreSQL',
            'host': 'localhost',
            'port': 5432,
            'user': 'testuser',
            'password': 'testpass'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect, \
             patch('src.core.connection_manager.pd.read_sql') as mock_read_sql:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_engine.connect.return_value = mock_connection
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Mock read_sql to return a DataFrame with database names
            mock_df = pd.DataFrame({'datname': ['db1', 'db2', 'db3']})
            mock_read_sql.return_value = mock_df
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Get available databases
            databases = connection.get_available_databases()
            
            # Check that read_sql was called with the correct query
            mock_read_sql.assert_called_with(
                "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname",
                mock_connection
            )
            
            # Check that the correct databases were returned
            self.assertEqual(databases, ['db1', 'db2', 'db3'])
    
    def test_use_database(self):
        """Test switching to a different database"""
        connection_params = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'initial_db'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Reset the mocks to check the next call
            mock_create_engine.reset_mock()
            
            # Switch to a different database
            result = connection.use_database('new_db')
            
            # Check that the database was switched
            self.assertTrue(result)
            self.assertEqual(connection.params['database'], 'new_db')
            
            # Check that create_engine was called with the new connection string
            mock_create_engine.assert_called_once_with(
                'mysql+pymysql://testuser:testpass@localhost:3306/new_db'
            )
    
    def test_use_database_updates_connection_manager(self):
        """Test that use_database updates the connection parameters in the connection manager"""
        # Create a mock connection manager
        mock_connection_manager = MagicMock()
        mock_connection_manager.connection_params = {
            'test_connection': {
                'name': 'test_connection',
                'type': 'MySQL',
                'host': 'localhost',
                'port': 3306,
                'user': 'testuser',
                'password': 'testpass',
                'database': 'initial_db'
            }
        }
        
        connection_params = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'initial_db'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Set the connection manager reference
            connection.connection_manager = mock_connection_manager
            
            # Switch to a different database
            result = connection.use_database('new_db')
            
            # Check that the database was switched
            self.assertTrue(result)
            
            # Check that the connection parameters were updated in the connection manager
            self.assertEqual(
                mock_connection_manager.connection_params['test_connection']['database'],
                'new_db'
            )
            
            # Check that save_connections was called
            mock_connection_manager.save_connections.assert_called_once()
    
    def test_use_database_same_database(self):
        """Test switching to the same database (should be a no-op)"""
        connection_params = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'test_db'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Reset the mocks to check the next call
            mock_create_engine.reset_mock()
            
            # Try to switch to the same database
            result = connection.use_database('test_db')
            
            # Check that the method returned False (no change)
            self.assertFalse(result)
            
            # Check that create_engine was not called again
            mock_create_engine.assert_not_called()
    
    def test_deselect_database(self):
        """Test deselecting a database"""
        connection_params = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'test_db'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Reset the mocks to check the next call
            mock_create_engine.reset_mock()
            
            # Deselect the database
            result = connection.deselect_database()
            
            # Check that the method returned True (database was deselected)
            self.assertTrue(result)
            
            # Check that the database parameter was removed
            self.assertNotIn('database', connection.params)
            
            # Check that create_engine was called with the connection string without a database
            mock_create_engine.assert_called_once_with(
                'mysql+pymysql://testuser:testpass@localhost:3306/'
            )
    
    def test_deselect_database_updates_connection_manager(self):
        """Test that deselect_database updates the connection parameters in the connection manager"""
        # Create a mock connection manager
        mock_connection_manager = MagicMock()
        mock_connection_manager.connection_params = {
            'test_connection': {
                'name': 'test_connection',
                'type': 'MySQL',
                'host': 'localhost',
                'port': 3306,
                'user': 'testuser',
                'password': 'testpass',
                'database': 'test_db'
            }
        }
        
        connection_params = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'test_db'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Set the connection manager reference
            connection.connection_manager = mock_connection_manager
            
            # Deselect the database
            result = connection.deselect_database()
            
            # Check that the database was deselected
            self.assertTrue(result)
            
            # Check that the database parameter was removed from the connection parameters in the connection manager
            self.assertNotIn('database', mock_connection_manager.connection_params['test_connection'])
            
            # Check that save_connections was called
            mock_connection_manager.save_connections.assert_called_once()
    
    def test_deselect_database_already_no_database(self):
        """Test deselecting a database when no database is selected (should be a no-op)"""
        connection_params = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass'
            # No database parameter
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Reset the mocks to check the next call
            mock_create_engine.reset_mock()
            
            # Mock get_database_name to return "(No database selected)"
            connection.get_database_name = MagicMock(return_value="(No database selected)")
            
            # Try to deselect the database
            result = connection.deselect_database()
            
            # Check that the method returned False (no change)
            self.assertFalse(result)
            
            # Check that create_engine was not called again
            mock_create_engine.assert_not_called()
    
    def test_execute_query(self):
        """Test executing a query"""
        connection_params = {
            'name': 'test_connection',
            'type': 'SQLite',
            'database': ':memory:'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Mock pd.read_sql to return a test DataFrame
            test_df = pd.DataFrame({'id': [1, 2], 'name': ['Test1', 'Test2']})
            with patch('pandas.read_sql', return_value=test_df) as mock_read_sql:
                # Create the connection
                connection = DatabaseConnection(connection_params)
                
                # Execute a test query
                result = connection.execute_query('SELECT * FROM test')
                
                # Check that read_sql was called with the correct parameters
                mock_read_sql.assert_called_once_with('SELECT * FROM test', mock_engine)
                
                # Check that the result is the test DataFrame
                pd.testing.assert_frame_equal(result, test_df)
    
    def test_execute_non_query(self):
        """Test executing a non-query statement"""
        connection_params = {
            'name': 'test_connection',
            'type': 'SQLite',
            'database': ':memory:'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine, inspector, and connection
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.rowcount = 2  # Simulate 2 rows affected
            
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            mock_connection.execute.return_value = mock_result
            
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Execute a test non-query
            result = connection.execute_non_query("INSERT INTO test VALUES (1, 'Test')")
            
            # Check that execute was called with the correct parameters
            mock_connection.execute.assert_called_once()
            self.assertEqual(mock_connection.execute.call_args[0][0].text, 
                             "INSERT INTO test VALUES (1, 'Test')")
            
            # Check that the result is the rowcount
            self.assertEqual(result, 2)
    
    def test_get_tables(self):
        """Test getting tables from the database"""
        connection_params = {
            'name': 'test_connection',
            'type': 'SQLite',
            'database': ':memory:'
        }
        
        with patch('src.core.connection_manager.create_engine') as mock_create_engine, \
             patch('src.core.connection_manager.inspect') as mock_inspect:
            # Mock the SQLAlchemy engine and inspector
            mock_engine = MagicMock()
            mock_inspector = MagicMock()
            mock_inspector.get_table_names.return_value = ['table1', 'table2']
            
            mock_create_engine.return_value = mock_engine
            mock_inspect.return_value = mock_inspector
            
            # Create the connection
            connection = DatabaseConnection(connection_params)
            
            # Get the tables
            tables = connection.get_tables()
            
            # Check that get_table_names was called
            mock_inspector.get_table_names.assert_called_once()
            
            # Check that the tables list is correct
            self.assertEqual(tables, ['table1', 'table2'])


if __name__ == '__main__':
    unittest.main()