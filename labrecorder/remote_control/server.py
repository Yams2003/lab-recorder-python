"""
TCP server for remote control of Lab Recorder.
"""

import socket
import threading
from typing import Callable, Optional

from .commands import CommandHandler


class RemoteControlServer:
    """TCP server for remote control interface."""
    
    def __init__(self, recorder_interface, port: int = 22345):
        """
        Initialize remote control server.
        
        Args:
            recorder_interface: Object that provides recorder methods
            port: TCP port to listen on
        """
        self.recorder = recorder_interface
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.server_thread: Optional[threading.Thread] = None
        self.active = False
        
        # Command handler for processing commands
        self.command_handler = CommandHandler(recorder_interface)
        
    def start(self) -> bool:
        """
        Start the TCP server.
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.port))
            self.server_socket.listen(5)
            self.active = True
            
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            print(f"Remote control server started on port {self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to start remote control server: {e}")
            self.active = False
            return False
    
    def stop(self) -> None:
        """Stop the TCP server."""
        if self.server_socket:
            self.active = False
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            print("Remote control server stopped")
    
    def _server_loop(self) -> None:
        """Main server loop for accepting connections."""
        while self.active:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Remote control connection from {address}")
                
                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()
                
            except socket.error:
                if self.active:
                    print("Remote control server socket error")
                break
    
    def _handle_client(self, client_socket: socket.socket) -> None:
        """
        Handle commands from a connected client.
        
        Args:
            client_socket: Connected client socket
        """
        try:
            while self.active:
                # Receive command from client
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                command = data.decode('utf-8').strip()
                print(f"Remote control command: {command}")
                
                # Process command and send response
                response = self.command_handler.process_command(command)
                if response:
                    client_socket.send((response + '\n').encode('utf-8'))
                    
        except Exception as e:
            print(f"Remote control client error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass 