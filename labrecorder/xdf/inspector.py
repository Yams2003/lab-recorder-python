#!/usr/bin/env python3
"""
Simple XDF File Inspector
Reads and displays basic information about XDF file contents
"""

import struct
import sys
import xml.etree.ElementTree as ET

# XDF Magic Code and Chunk Tags
XDF_MAGIC = b"XDF:"
FILE_HEADER_TAG = 1
STREAM_HEADER_TAG = 2
SAMPLES_TAG = 3
CLOCK_OFFSET_TAG = 4
BOUNDARY_TAG = 5
STREAM_FOOTER_TAG = 6

CHUNK_NAMES = {
    FILE_HEADER_TAG: "FileHeader",
    STREAM_HEADER_TAG: "StreamHeader", 
    SAMPLES_TAG: "Samples",
    CLOCK_OFFSET_TAG: "ClockOffset",
    BOUNDARY_TAG: "Boundary",
    STREAM_FOOTER_TAG: "StreamFooter"
}

def inspect_xdf_file(filename):
    """Inspect XDF file and print summary information."""
    
    print(f"=== XDF File Inspector ===")
    print(f"File: {filename}")
    
    try:
        with open(filename, 'rb') as f:
            # Check magic header
            magic = f.read(4)
            if magic != XDF_MAGIC:
                print(f"ERROR: Invalid XDF file. Expected 'XDF:', got {magic}")
                return False
            
            print(f"✓ Valid XDF magic header: {magic.decode()}")
            
            chunk_counts = {}
            stream_info = {}
            total_samples = 0
            file_size = f.seek(0, 2)  # Seek to end to get file size
            f.seek(4)  # Reset to position after magic
            
            print(f"File size: {file_size} bytes ({file_size/1024:.1f} KB)")
            print("\n=== Chunks ===")
            
            chunk_num = 0
            while f.tell() < file_size:
                try:
                    # Read chunk header
                    length_bytes_data = f.read(4)
                    if len(length_bytes_data) < 4:
                        break
                    
                    length_bytes = struct.unpack('<I', length_bytes_data)[0]
                    if length_bytes != 4:
                        print(f"Warning: Unexpected length field size: {length_bytes}")
                    
                    payload_length_data = f.read(4)
                    if len(payload_length_data) < 4:
                        break
                    payload_length = struct.unpack('<I', payload_length_data)[0]
                    
                    tag_data = f.read(2)
                    if len(tag_data) < 2:
                        break
                    tag = struct.unpack('<H', tag_data)[0]
                    
                    # Read payload
                    payload = f.read(payload_length)
                    if len(payload) < payload_length:
                        print(f"Warning: Expected {payload_length} bytes, got {len(payload)}")
                        break
                    
                    chunk_num += 1
                    chunk_name = CHUNK_NAMES.get(tag, f"Unknown({tag})")
                    chunk_counts[chunk_name] = chunk_counts.get(chunk_name, 0) + 1
                    
                    print(f"Chunk {chunk_num}: {chunk_name} (tag={tag}, {payload_length} bytes)")
                    
                    # Parse specific chunk types
                    if tag in [STREAM_HEADER_TAG, STREAM_FOOTER_TAG]:
                        # Stream-specific chunks have stream_id in payload
                        if len(payload) >= 4:
                            stream_id = struct.unpack('<I', payload[:4])[0]
                            xml_content = payload[4:].decode('utf-8', errors='ignore')
                            try:
                                root = ET.fromstring(xml_content)
                                name = root.find('name')
                                stype = root.find('type') 
                                channels = root.find('channel_count')
                                srate = root.find('nominal_srate')
                                
                                name_text = name.text if name is not None else "Unknown"
                                type_text = stype.text if stype is not None else "Unknown"
                                channel_text = channels.text if channels is not None else "Unknown"
                                srate_text = srate.text if srate is not None else "Unknown"
                                
                                print(f"  Stream ID: {stream_id}")
                                print(f"  Name: {name_text}")
                                print(f"  Type: {type_text}")
                                print(f"  Channels: {channel_text}")
                                print(f"  Sample Rate: {srate_text}")
                                
                                if tag == STREAM_HEADER_TAG:
                                    stream_info[stream_id] = {
                                        'name': name_text,
                                        'type': type_text,
                                        'channels': channel_text,
                                        'srate': srate_text,
                                        'sample_count': 0
                                    }
                            except ET.ParseError as e:
                                print(f"  Warning: Could not parse XML: {e}")
                    
                    elif tag == SAMPLES_TAG:
                        # Samples chunk
                        if len(payload) >= 4:
                            stream_id = struct.unpack('<I', payload[:4])[0]
                            samples_data = payload[4:]
                            
                            # Try to estimate number of samples (simplified)
                            if len(samples_data) > 1:
                                timestamp_bytes = samples_data[0]  # M value
                                if timestamp_bytes == 8:  # Double precision timestamps
                                    remaining = samples_data[1:]
                                    # Count timestamps (each is 8 bytes)
                                    timestamps_end = 0
                                    try:
                                        while timestamps_end < len(remaining) and timestamps_end % 8 == 0:
                                            timestamps_end += 8
                                            # Check if we can unpack a valid timestamp
                                            if timestamps_end <= len(remaining):
                                                ts = struct.unpack('<d', remaining[timestamps_end-8:timestamps_end])[0]
                                                if ts <= 0 or ts > 1e10:  # Sanity check
                                                    timestamps_end -= 8
                                                    break
                                            else:
                                                break
                                        
                                        num_samples = timestamps_end // 8
                                        total_samples += num_samples
                                        if stream_id in stream_info:
                                            stream_info[stream_id]['sample_count'] += num_samples
                                        
                                        print(f"  Stream ID: {stream_id}, ~{num_samples} samples")
                                    except:
                                        print(f"  Stream ID: {stream_id}, sample data present")
                    
                    elif tag == CLOCK_OFFSET_TAG:
                        if len(payload) >= 20:  # stream_id (4) + time (8) + offset (8)
                            stream_id = struct.unpack('<I', payload[:4])[0]
                            time_val, offset_val = struct.unpack('<dd', payload[4:20])
                            print(f"  Stream ID: {stream_id}, Time: {time_val:.4f}, Offset: {offset_val:.6f}")
                    
                except struct.error as e:
                    print(f"Error reading chunk {chunk_num}: {e}")
                    break
                except Exception as e:
                    print(f"Unexpected error in chunk {chunk_num}: {e}")
                    break
            
            print(f"\n=== Summary ===")
            print(f"Total chunks: {chunk_num}")
            for chunk_type, count in chunk_counts.items():
                print(f"  {chunk_type}: {count}")
            
            print(f"\n=== Streams ===")
            for stream_id, info in stream_info.items():
                print(f"Stream {stream_id}: {info['name']} ({info['type']})")
                print(f"  Channels: {info['channels']}, Rate: {info['srate']} Hz")
                print(f"  Samples recorded: {info['sample_count']}")
            
            print(f"\nTotal samples across all streams: {total_samples}")
            
            return True
            
    except FileNotFoundError:
        print(f"ERROR: File '{filename}' not found")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python xdf_inspector.py <xdf_file>")
        sys.exit(1)
    
    filename = sys.argv[1]
    success = inspect_xdf_file(filename)
    sys.exit(0 if success else 1) 