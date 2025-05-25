# file_protocol.py
import json
import base64
import os
import logging

class FileProtocol:
    def __init__(self, storage_path="files"):
        """
        Initialize FileProtocol with storage directory
        """
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            logging.info(f"Created storage directory: {self.storage_path}")

    def proses_string(self, command_string):
        """
        Process command string and return JSON response
        Supported commands:
        - UPLOAD <filename> <base64_content>
        - GET <filename>
        - LIST
        - DELETE <filename>
        """
        try:
            # Split command into parts
            parts = command_string.strip().split(' ', 2)
            
            if not parts:
                return json.dumps({
                    'status': 'ERROR',
                    'data': 'Empty command'
                })
            
            command = parts[0].upper()
            
            if command == 'UPLOAD':
                return self._handle_upload(parts)
            elif command == 'GET':
                return self._handle_get(parts)
            elif command == 'LIST':
                return self._handle_list()
            elif command == 'DELETE':
                return self._handle_delete(parts)
            else:
                return json.dumps({
                    'status': 'ERROR',
                    'data': f'Unknown command: {command}'
                })
                
        except Exception as e:
            logging.error(f"Error processing command: {str(e)}")
            return json.dumps({
                'status': 'ERROR',
                'data': f'Server error: {str(e)}'
            })

    def _handle_upload(self, parts):
        """Handle UPLOAD command"""
        if len(parts) < 3:
            return json.dumps({
                'status': 'ERROR',
                'data': 'UPLOAD command requires filename and content'
            })
        
        try:
            filename = parts[1]
            base64_content = parts[2]
            
            # Validate filename
            if not self._is_valid_filename(filename):
                return json.dumps({
                    'status': 'ERROR',
                    'data': 'Invalid filename'
                })
            
            # Decode base64 content
            try:
                file_content = base64.b64decode(base64_content)
            except Exception as e:
                return json.dumps({
                    'status': 'ERROR',
                    'data': 'Invalid base64 content'
                })
            
            # Write file to storage
            file_path = os.path.join(self.storage_path, filename)
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            file_size = len(file_content)
            logging.info(f"File uploaded: {filename} ({file_size} bytes)")
            
            return json.dumps({
                'status': 'OK',
                'data': f'File {filename} uploaded successfully',
                'file_size': file_size
            })
            
        except Exception as e:
            logging.error(f"Upload error: {str(e)}")
            return json.dumps({
                'status': 'ERROR',
                'data': f'Upload failed: {str(e)}'
            })

    def _handle_get(self, parts):
        """Handle GET command"""
        if len(parts) < 2:
            return json.dumps({
                'status': 'ERROR',
                'data': 'GET command requires filename'
            })
        
        try:
            filename = parts[1]
            
            # Validate filename
            if not self._is_valid_filename(filename):
                return json.dumps({
                    'status': 'ERROR',
                    'data': 'Invalid filename'
                })
            
            file_path = os.path.join(self.storage_path, filename)
            
            # Check if file exists
            if not os.path.exists(file_path):
                return json.dumps({
                    'status': 'ERROR',
                    'data': f'File not found: {filename}'
                })
            
            # Read and encode file
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            base64_content = base64.b64encode(file_content).decode()
            file_size = len(file_content)
            
            logging.info(f"File downloaded: {filename} ({file_size} bytes)")
            
            return json.dumps({
                'status': 'OK',
                'data': f'File {filename} retrieved successfully',
                'data_file': base64_content,
                'file_size': file_size
            })
            
        except Exception as e:
            logging.error(f"Get error: {str(e)}")
            return json.dumps({
                'status': 'ERROR',
                'data': f'Get failed: {str(e)}'
            })

    def _handle_list(self):
        """Handle LIST command"""
        try:
            files = []
            for filename in os.listdir(self.storage_path):
                file_path = os.path.join(self.storage_path, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_info = {
                        'filename': filename,
                        'size': file_size
                    }
                    files.append(file_info)
            
            return json.dumps({
                'status': 'OK',
                'data': 'File list retrieved successfully',
                'files': files,
                'count': len(files)
            })
            
        except Exception as e:
            logging.error(f"List error: {str(e)}")
            return json.dumps({
                'status': 'ERROR',
                'data': f'List failed: {str(e)}'
            })

    def _handle_delete(self, parts):
        """Handle DELETE command"""
        if len(parts) < 2:
            return json.dumps({
                'status': 'ERROR',
                'data': 'DELETE command requires filename'
            })
        
        try:
            filename = parts[1]
            
            # Validate filename
            if not self._is_valid_filename(filename):
                return json.dumps({
                    'status': 'ERROR',
                    'data': 'Invalid filename'
                })
            
            file_path = os.path.join(self.storage_path, filename)
            
            # Check if file exists
            if not os.path.exists(file_path):
                return json.dumps({
                    'status': 'ERROR',
                    'data': f'File not found: {filename}'
                })
            
            # Delete file
            os.remove(file_path)
            logging.info(f"File deleted: {filename}")
            
            return json.dumps({
                'status': 'OK',
                'data': f'File {filename} deleted successfully'
            })
            
        except Exception as e:
            logging.error(f"Delete error: {str(e)}")
            return json.dumps({
                'status': 'ERROR',
                'data': f'Delete failed: {str(e)}'
            })

    def _is_valid_filename(self, filename):
        """
        Validate filename to prevent directory traversal attacks
        """
        if not filename:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # Check filename length
        if len(filename) > 255:
            return False
        
        return True