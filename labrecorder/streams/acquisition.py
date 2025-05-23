"""
Data acquisition threads for LSL streams.
"""

import time
import threading
import pylsl
from typing import List, Tuple, Callable


class AcquisitionThread:
    """Thread for acquiring data from a single LSL stream."""
    
    def __init__(self, stream_uid: str, stream_info: pylsl.StreamInfo, 
                 inlet: pylsl.StreamInlet, data_callback: Callable):
        """
        Initialize acquisition thread.
        
        Args:
            stream_uid: Unique identifier for the stream
            stream_info: LSL StreamInfo object
            inlet: LSL StreamInlet for data acquisition
            data_callback: Callback function for data (stream_uid, samples, timestamps)
        """
        self.stream_uid = stream_uid
        self.stream_info = stream_info
        self.inlet = inlet
        self.data_callback = data_callback
        
        self.thread = None
        self.running = False
        self.last_timestamp = None
        
        # Calculate max samples per pull based on sampling rate
        self.max_samples_per_pull = self._calculate_max_samples()
        
    def _calculate_max_samples(self) -> int:
        """Calculate optimal number of samples to pull at once."""
        nominal_rate = self.stream_info.nominal_srate()
        if nominal_rate > 0:
            max_samples = int(nominal_rate)
        else:
            max_samples = 100  # For irregular rate streams
            
        if max_samples == 0:
            max_samples = 1
        elif max_samples > 500:
            max_samples = 500  # Cap to avoid huge chunks
            
        return max_samples
    
    def start(self) -> None:
        """Start the acquisition thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self.thread.start()
        print(f"Started acquisition for {self.stream_info.name()} (UID: {self.stream_uid})")
    
    def stop(self) -> None:
        """Stop the acquisition thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        print(f"Stopped acquisition for {self.stream_info.name()} (UID: {self.stream_uid})")
    
    def _acquisition_loop(self) -> None:
        """Main acquisition loop running in the thread."""
        stream_name = self.stream_info.name()
        buffer_list = []  # Local buffer for this thread
        
        try:
            while self.running:
                # Pull data from the stream
                samples, timestamps = self.inlet.pull_chunk(
                    timeout=0.1, 
                    max_samples=self.max_samples_per_pull
                )
                
                if timestamps:
                    buffer_list.append((samples, timestamps))
                    self.last_timestamp = timestamps[-1]
                    
                    # Send data to callback in batches to avoid too frequent calls
                    if len(buffer_list) > 10:
                        for samples_chunk, timestamps_chunk in buffer_list:
                            self.data_callback(self.stream_uid, samples_chunk, timestamps_chunk)
                        buffer_list.clear()
                        
                elif self.inlet.was_clock_reset():
                    print(f"Clock reset detected for stream {stream_name}. Re-evaluating sync.")
                    # Handle clock reset if necessary
                    # Could write a new ClockOffset chunk here
                    pass
                    
                else:
                    # No data received, small sleep to prevent busy-waiting
                    time.sleep(0.001)
                    
        except Exception as e:
            print(f"Error in acquisition thread for {stream_name}: {e}")
        finally:
            # Send any remaining buffered data
            if buffer_list:
                for samples_chunk, timestamps_chunk in buffer_list:
                    self.data_callback(self.stream_uid, samples_chunk, timestamps_chunk)
            print(f"Acquisition thread for {stream_name} finished.")


class AcquisitionManager:
    """Manages multiple acquisition threads."""
    
    def __init__(self, data_callback: Callable):
        """
        Initialize acquisition manager.
        
        Args:
            data_callback: Callback function for data (stream_uid, samples, timestamps)
        """
        self.data_callback = data_callback
        self.acquisition_threads = {}
        self.buffer_lock = threading.Lock()
        
    def add_stream(self, stream_uid: str, stream_info: pylsl.StreamInfo, 
                   inlet: pylsl.StreamInlet) -> None:
        """
        Add a stream for acquisition.
        
        Args:
            stream_uid: Stream unique identifier
            stream_info: LSL StreamInfo object
            inlet: LSL StreamInlet for data acquisition
        """
        thread = AcquisitionThread(stream_uid, stream_info, inlet, self.data_callback)
        self.acquisition_threads[stream_uid] = thread
        
    def start_all(self) -> None:
        """Start acquisition for all streams."""
        for thread in self.acquisition_threads.values():
            thread.start()
            
    def stop_all(self) -> None:
        """Stop acquisition for all streams."""
        for thread in self.acquisition_threads.values():
            thread.stop()
        self.acquisition_threads.clear()
        
    def get_last_timestamps(self) -> dict:
        """Get last timestamp for each stream."""
        return {
            uid: thread.last_timestamp 
            for uid, thread in self.acquisition_threads.items()
            if thread.last_timestamp is not None
        } 