"""
Patch for the DatabaseConnection class to handle string values for port and save_password
"""

from src.core.connection_manager import DatabaseConnection

# Save the original _build_connection_string method
original_build_connection_string = DatabaseConnection._build_connection_string

def patched_build_connection_string(self):
    """Patched version of _build_connection_string that handles string values for port"""
    # Convert port to int if it's a string
    if 'port' in self.params and isinstance(self.params['port'], str):
        try:
            # Only try to convert if the string is not empty
            if self.params['port'].strip():
                self.params['port'] = int(self.params['port'])
            else:
                # Use default port based on database type
                if self.params['type'] == 'MySQL':
                    self.params['port'] = 3306
                elif self.params['type'] == 'PostgreSQL':
                    self.params['port'] = 5432
                else:
                    # Default fallback
                    self.params['port'] = 0
        except ValueError:
            # If conversion fails, use default port based on database type
            if self.params['type'] == 'MySQL':
                self.params['port'] = 3306
            elif self.params['type'] == 'PostgreSQL':
                self.params['port'] = 5432
            else:
                # Default fallback
                self.params['port'] = 0
            
    # Convert save_password to bool if it's a string
    if 'save_password' in self.params and isinstance(self.params['save_password'], str):
        self.params['save_password'] = self.params['save_password'].lower() == 'true'
        
    # Call the original method
    return original_build_connection_string(self)

# Replace the original method with the patched version
DatabaseConnection._build_connection_string = patched_build_connection_string