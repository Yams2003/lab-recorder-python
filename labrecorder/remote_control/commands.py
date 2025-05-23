"""
Command handlers for remote control interface.
"""

import json
import re
import os
import threading
from typing import Callable, Any


class CommandHandler:
    """Handles parsing and execution of remote control commands."""
    
    def __init__(self, recorder_interface):
        """
        Initialize command handler.
        
        Args:
            recorder_interface: Object that provides recorder methods
        """
        self.recorder = recorder_interface
        self.control_lock = threading.Lock()
        
    def process_command(self, command: str) -> str:
        """
        Process a remote control command and return response.
        
        Args:
            command: Command string to process
            
        Returns:
            Response string
        """
        try:
            with self.control_lock:
                parts = command.split()
                if not parts:
                    return "ERROR: Empty command"
                
                cmd = parts[0].lower()
                
                if cmd == "select":
                    return self._handle_select(parts)
                elif cmd == "start":
                    return self._handle_start()
                elif cmd == "stop":
                    return self._handle_stop()
                elif cmd == "update":
                    return self._handle_update()
                elif cmd == "filename":
                    return self._handle_filename(command)
                elif cmd == "status":
                    return self._handle_status()
                elif cmd == "streams":
                    return self._handle_streams()
                else:
                    return f"ERROR: Unknown command: {cmd}"
                    
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def _handle_select(self, parts: list) -> str:
        """Handle stream selection commands."""
        if len(parts) < 2:
            return "ERROR: select requires argument (all/none)"
        
        option = parts[1].lower()
        if option == "all":
            try:
                count = self.recorder.select_all_streams()
                return f"OK: Selected {count} streams"
            except Exception as e:
                return f"ERROR: {str(e)}"
                
        elif option == "none":
            try:
                self.recorder.deselect_all_streams()
                return "OK: Deselected all streams"
            except Exception as e:
                return f"ERROR: {str(e)}"
        else:
            return f"ERROR: Unknown select option: {option}"
    
    def _handle_start(self) -> str:
        """Handle start recording command."""
        try:
            if self.recorder.is_recording():
                return "ERROR: Already recording"
            
            if not self.recorder.has_selected_streams():
                return "ERROR: No streams selected"
            
            self.recorder.start_recording()
            return "OK: Recording started"
        except Exception as e:
            return f"ERROR: Failed to start recording: {str(e)}"
    
    def _handle_stop(self) -> str:
        """Handle stop recording command."""
        try:
            if not self.recorder.is_recording():
                return "ERROR: Not currently recording"
            
            self.recorder.stop_recording()
            return "OK: Recording stopped"
        except Exception as e:
            return f"ERROR: Failed to stop recording: {str(e)}"
    
    def _handle_update(self) -> str:
        """Handle update streams command."""
        try:
            count = self.recorder.update_streams()
            return f"OK: Found {count} streams"
        except Exception as e:
            return f"ERROR: Failed to update streams: {str(e)}"
    
    def _handle_filename(self, command: str) -> str:
        """Handle filename setting command."""
        try:
            if self.recorder.is_recording():
                return "ERROR: Cannot change filename while recording"
            
            # Parse filename command with parameters
            if '{' in command and '}' in command:
                return self._handle_filename_template(command)
            else:
                # Simple filename
                parts = command.split(maxsplit=1)
                if len(parts) > 1:
                    self.recorder.set_filename(parts[1])
                    return f"OK: Filename set to {parts[1]}"
                else:
                    return "ERROR: No filename specified"
                    
        except Exception as e:
            return f"ERROR: Failed to set filename: {str(e)}"
    
    def _handle_filename_template(self, command: str) -> str:
        """Handle filename command with template parameters."""
        # Extract parameters from braces: {key:value}
        params = {}
        pattern = r'\{(\w+):([^}]+)\}'
        matches = re.findall(pattern, command)
        
        for key, value in matches:
            params[key] = value
        
        # Build filename from template
        if 'template' not in params:
            return "ERROR: No template specified"
        
        filename = params['template']
        
        # Replace placeholders
        replacements = {
            '%p': params.get('participant', 'unknown'),
            '%s': params.get('session', 'default'),
            '%b': params.get('task', 'task'),
            '%n': params.get('run', '1'),
            '%a': params.get('acquisition', 'acq'),
            '%m': params.get('modality', 'data')
        }
        
        for placeholder, value in replacements.items():
            filename = filename.replace(placeholder, value)
        
        # Add root directory if specified
        if 'root' in params:
            filename = os.path.join(params['root'], filename)
        
        self.recorder.set_filename(filename)
        return f"OK: Filename set to {filename}"
    
    def _handle_status(self) -> str:
        """Handle status query command."""
        try:
            status = self.recorder.get_status()
            return f"OK: {json.dumps(status)}"
        except Exception as e:
            return f"ERROR: Failed to get status: {str(e)}"
    
    def _handle_streams(self) -> str:
        """Handle streams list command."""
        try:
            streams = self.recorder.get_stream_list()
            if not streams:
                return "ERROR: No streams found. Run 'update' first."
            return f"OK: {json.dumps(streams)}"
        except Exception as e:
            return f"ERROR: Failed to get streams: {str(e)}" 