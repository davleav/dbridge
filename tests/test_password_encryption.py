"""
Tests for the password encryption functionality in the connection manager
"""

import unittest
import os
import tempfile
import json
import pathlib
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.connection_manager import ConnectionManager


class TestPasswordEncryption(unittest.TestCase):
    """Test cases for the password encryption functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for the config
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Patch the _get_config_dir method to use our temporary directory
        self.config_dir_patcher = patch.object(
            ConnectionManager, 
            '_get_config_dir',
            return_value=pathlib.Path(self.temp_dir.name)
        )
        self.mock_config_dir = self.config_dir_patcher.start()
        
        # Create the connection manager
        self.connection_manager = ConnectionManager()
    
    def tearDown(self):
        """Clean up after tests"""
        # Stop the patcher
        self.config_dir_patcher.stop()
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_encryption_key_creation(self):
        """Test that an encryption key is created on initialization"""
        # Check that the key file exists
        key_file = pathlib.Path(self.temp_dir.name) / "encryption.key"
        self.assertTrue(key_file.exists())
        
        # Check that the key file has the correct permissions
        # Note: This test might fail on Windows due to different permission model
        if os.name != 'nt':  # Skip on Windows
            self.assertEqual(oct(key_file.stat().st_mode)[-3:], '600')
        
        # Check that the cipher was created
        self.assertTrue(hasattr(self.connection_manager, 'cipher'))
    
    def test_encrypt_decrypt_password(self):
        """Test encrypting and decrypting a password"""
        # Test with a simple password
        password = "test_password"
        encrypted = self.connection_manager.encrypt_password(password)
        
        # Check that the encrypted password is different from the original
        self.assertNotEqual(password, encrypted)
        
        # Check that we can decrypt it back to the original
        decrypted = self.connection_manager.decrypt_password(encrypted)
        self.assertEqual(password, decrypted)
        
        # Test with a complex password
        complex_password = "C0mpl3x!P@$$w0rd#123"
        encrypted = self.connection_manager.encrypt_password(complex_password)
        decrypted = self.connection_manager.decrypt_password(encrypted)
        self.assertEqual(complex_password, decrypted)
        
        # Test with an empty password
        empty_password = ""
        encrypted = self.connection_manager.encrypt_password(empty_password)
        self.assertIsNone(encrypted)  # Should return None for empty passwords
        
        # Test with None
        none_password = None
        encrypted = self.connection_manager.encrypt_password(none_password)
        self.assertIsNone(encrypted)  # Should return None for None passwords
    
    def test_save_connections_with_encrypted_password(self):
        """Test saving connections with encrypted passwords"""
        # Add a connection with save_password=True
        connection_params = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'save_password': True,
            'database': 'testdb'
        }
        self.connection_manager.connection_params['test_connection'] = connection_params
        
        # Mock json.dump to capture the saved data
        mock_json_dump = MagicMock()
        with patch('json.dump', mock_json_dump):
            # Save the connections
            self.connection_manager.save_connections()
            
            # Get the data that was passed to json.dump
            saved_data = mock_json_dump.call_args[0][0]
            
            # Check that the connection was included
            self.assertIn('test_connection', saved_data)
            
            # Check that the password was removed and encrypted_password was added
            self.assertEqual(saved_data['test_connection']['password'], '')
            self.assertIn('encrypted_password', saved_data['test_connection'])
            self.assertNotEqual(saved_data['test_connection']['encrypted_password'], 'testpass')
    
    def test_save_connections_without_encrypted_password(self):
        """Test saving connections without encrypted passwords"""
        # Add a connection with save_password=False
        connection_params = {
            'name': 'test_connection',
            'type': 'MySQL',
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'save_password': False,
            'database': 'testdb'
        }
        self.connection_manager.connection_params['test_connection'] = connection_params
        
        # Mock json.dump to capture the saved data
        mock_json_dump = MagicMock()
        with patch('json.dump', mock_json_dump):
            # Save the connections
            self.connection_manager.save_connections()
            
            # Get the data that was passed to json.dump
            saved_data = mock_json_dump.call_args[0][0]
            
            # Check that the connection was included
            self.assertIn('test_connection', saved_data)
            
            # Check that the password was removed and no encrypted_password was added
            self.assertEqual(saved_data['test_connection']['password'], '')
            self.assertNotIn('encrypted_password', saved_data['test_connection'])
    
    def test_load_connections_with_encrypted_password(self):
        """Test loading connections with encrypted passwords"""
        # Create a test password and encrypt it
        test_password = "testpass"
        encrypted_password = self.connection_manager.encrypt_password(test_password)
        
        # Create a mock connections file with an encrypted password
        mock_connections = {
            'test_connection': {
                'name': 'test_connection',
                'type': 'MySQL',
                'host': 'localhost',
                'port': 3306,
                'user': 'testuser',
                'password': '',
                'encrypted_password': encrypted_password,
                'database': 'testdb'
            }
        }
        
        # Mock the open function to return our mock data
        mock_file = mock_open(read_data=json.dumps(mock_connections))
        
        # Mock the exists method to return True
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_file):
            
            # Load the connections
            self.connection_manager.connection_params.clear()  # Clear existing connections
            self.connection_manager.load_connections()
            
            # Check that the connection was loaded with the decrypted password
            self.assertIn('test_connection', self.connection_manager.connection_params)
            loaded_connection = self.connection_manager.connection_params['test_connection']
            self.assertEqual(loaded_connection['password'], test_password)
            self.assertTrue(loaded_connection['save_password'])
    
    def test_load_connections_without_encrypted_password(self):
        """Test loading connections without encrypted passwords"""
        # Create a mock connections file without an encrypted password
        mock_connections = {
            'test_connection': {
                'name': 'test_connection',
                'type': 'MySQL',
                'host': 'localhost',
                'port': 3306,
                'user': 'testuser',
                'password': '',
                'database': 'testdb'
            }
        }
        
        # Mock the open function to return our mock data
        mock_file = mock_open(read_data=json.dumps(mock_connections))
        
        # Mock the exists method to return True
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_file):
            
            # Load the connections
            self.connection_manager.connection_params.clear()  # Clear existing connections
            self.connection_manager.load_connections()
            
            # Check that the connection was loaded without a password
            self.assertIn('test_connection', self.connection_manager.connection_params)
            loaded_connection = self.connection_manager.connection_params['test_connection']
            self.assertEqual(loaded_connection['password'], '')
            self.assertNotIn('save_password', loaded_connection)


if __name__ == '__main__':
    unittest.main()