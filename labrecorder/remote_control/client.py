#!/usr/bin/env python3
"""
Simple TCP client to test remote control of LabRecorder
"""

import socket
import sys
import time

def send_command(host='localhost', port=22345, command='status'):
    """Send a command to the lab recorder and return the response."""
    try:
        # Create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        sock.connect((host, port))
        
        # Send command
        sock.send((command + '\n').encode('utf-8'))
        
        # Receive response
        response = sock.recv(1024).decode('utf-8').strip()
        
        sock.close()
        return response
        
    except socket.error as e:
        return f"ERROR: Connection failed - {e}"
    except Exception as e:
        return f"ERROR: {e}"

def interactive_client(host='localhost', port=22345):
    """Interactive client for sending commands."""
    print(f"Lab Recorder Remote Control Client")
    print(f"Connecting to {host}:{port}")
    print("Available commands:")
    print("  select all    - Select all streams")
    print("  select none   - Deselect all streams") 
    print("  start         - Start recording")
    print("  stop          - Stop recording")
    print("  update        - Update stream list")
    print("  status        - Get recorder status")
    print("  streams       - List available streams")
    print("  filename <name> - Set filename")
    print("  quit          - Exit client")
    print()
    
    while True:
        try:
            command = input("Remote> ").strip()
            if not command:
                continue
                
            if command.lower() in ['quit', 'exit', 'q']:
                break
                
            response = send_command(host, port, command)
            print(f"Response: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_client()
    elif len(sys.argv) == 2:
        # Single command mode
        command = sys.argv[1]
        response = send_command(command=command)
        print(response)
    else:
        # Command with arguments
        command = ' '.join(sys.argv[1:])
        response = send_command(command=command)
        print(response)

if __name__ == "__main__":
    main() 