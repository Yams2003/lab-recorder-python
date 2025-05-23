import gzip
import xml.etree.ElementTree as ET
import struct
import time
import numpy as np
import pylsl
from pylsl import cf_float32, cf_double64, cf_string, cf_int32, cf_int16, cf_int8, cf_int64

# XDF Magic Code
XDF_MAGIC = b"XDF:"

# Chunk Tags (integer codes)
FILE_HEADER_TAG = 1
STREAM_HEADER_TAG = 2
SAMPLES_TAG = 3
CLOCK_OFFSET_TAG = 4
BOUNDARY_TAG = 5
STREAM_FOOTER_TAG = 6

# Mapping from pylsl.cf_xxx constants to string representations
LSL_CF_TO_STRING = {
    cf_float32: "float32",
    cf_double64: "double64",
    cf_string: "string",
    cf_int32: "int32",
    cf_int16: "int16",
    cf_int8: "int8",
    cf_int64: "int64",
}

# Try to add cf_undefined if it exists in pylsl
try:
    from pylsl import cf_undefined
    LSL_CF_TO_STRING[cf_undefined] = "undefined"
except (ImportError, AttributeError):
    # If cf_undefined doesn't exist, use 0 as the key
    LSL_CF_TO_STRING[0] = "undefined"

# From LSL channel format string to struct pack format char
LSL_STRING_TO_STRUCT_FORMAT = {
    "float32": "f",
    "double64": "d",
    "string": "s",  # Special handling for strings
    "int32": "i",
    "int16": "h",
    "int8": "b",
    "int64": "q",
    "undefined": "" # For undefined, should probably not write samples
}

class SimpleXDFWriter:
    def __init__(self, filename):
        self.filename = filename
        self.file = None
        self.stream_id_counter = 1
        # uid -> {lsl_info, xdf_stream_id, struct_format_char, lsl_channel_format_str}
        self.stream_info_map = {}

    def open(self):
        self.file = open(self.filename, "wb")
        self.file.write(XDF_MAGIC)
        # Write FileHeader chunk (minimal)
        file_header_content = "<info><version>1.0</version></info>"
        self._write_chunk(FILE_HEADER_TAG, file_header_content)
        print(f"XDF file {self.filename} opened and FileHeader written.")

    def _write_chunk(self, tag, content, stream_id=0):
        if not self.file:
            raise IOError("File not open. Call open() first.")

        content_bytes = content.encode('utf-8') if isinstance(content, str) else content

        payload = bytearray()
        # For stream-specific chunks, the stream_id is part of the payload
        if tag in [STREAM_HEADER_TAG, SAMPLES_TAG, STREAM_FOOTER_TAG, CLOCK_OFFSET_TAG]:
            payload.extend(struct.pack("<I", stream_id)) # Little-endian uint32 for StreamID
        
        payload.extend(content_bytes)
        
        # Length of the chunk itself (varint, but XDF spec often shows fixed size for this length field)
        # We'll use 4 bytes for the length of the length, then 4 bytes for the length itself for simplicity like pyxdf.
        self.file.write(struct.pack("<I", 4)) # Number of bytes for length field (always 4 for uint32 length)
        self.file.write(struct.pack("<I", len(payload))) # Length of the upcoming payload (uint32)
        self.file.write(struct.pack("<H", tag)) # Chunk Tag (uint16)
        self.file.write(payload)
        # print(f"Wrote chunk: Tag={tag}, StreamID={stream_id if tag in [STREAM_HEADER_TAG, SAMPLES_TAG, STREAM_FOOTER_TAG, CLOCK_OFFSET_TAG] else 'N/A'}, PayloadLength={len(payload)}")

    def add_stream(self, lsl_stream_info: pylsl.StreamInfo):
        if not self.file:
            raise IOError("File not open. Call open() first.")

        xdf_stream_id = self.stream_id_counter
        self.stream_id_counter += 1

        uid = lsl_stream_info.uid()
        lsl_channel_format_int = lsl_stream_info.channel_format()
        lsl_channel_format_str = LSL_CF_TO_STRING.get(lsl_channel_format_int, "undefined")
        struct_fmt_char = LSL_STRING_TO_STRUCT_FORMAT.get(lsl_channel_format_str, None)

        if struct_fmt_char is None and lsl_channel_format_str not in ["string", "undefined"]:
            print(f"Warning: Unsupported LSL channel format '{lsl_channel_format_str}' (int: {lsl_channel_format_int}) for stream {uid}. Samples may not be written correctly.")

        self.stream_info_map[uid] = {
            "lsl_info": lsl_stream_info,
            "xdf_stream_id": xdf_stream_id,
            "struct_format_char": struct_fmt_char,
            "lsl_channel_format_str": lsl_channel_format_str
        }

        root = ET.Element("info")
        ET.SubElement(root, "name").text = lsl_stream_info.name()
        ET.SubElement(root, "type").text = lsl_stream_info.type()
        ET.SubElement(root, "channel_count").text = str(lsl_stream_info.channel_count())
        ET.SubElement(root, "nominal_srate").text = str(lsl_stream_info.nominal_srate())
        ET.SubElement(root, "channel_format").text = lsl_channel_format_str
        ET.SubElement(root, "source_id").text = uid

        desc_outer = ET.SubElement(root, "desc") # XDF standard often has <desc> as a container
        lsl_desc = lsl_stream_info.desc()
        if lsl_desc is not None:
            try:
                # Try to get the first child if it exists
                child = lsl_desc.first_child()
                if not child.empty():
                    while not child.empty():
                        el = ET.SubElement(desc_outer, child.name())
                        el.text = child.child_value()
                        # Handle one level of children if they exist
                        sub_child = child.first_child()
                        while not sub_child.empty():
                            sub_el = ET.SubElement(el, sub_child.name())
                            sub_el.text = sub_child.child_value()
                            sub_child = sub_child.next_sibling()
                        child = child.next_sibling()
            except Exception as e:
                print(f"Warning: Could not process LSL description for stream {uid}: {e}")
                ET.SubElement(desc_outer, "source_format").text = "LSL_minimal_description"
        else:
            ET.SubElement(desc_outer, "source_format").text = "LSL_minimal_description"

        xml_content_string = ET.tostring(root, encoding="utf-8").decode('utf-8')
        self._write_chunk(STREAM_HEADER_TAG, xml_content_string, stream_id=xdf_stream_id)
        print(f"Added stream to XDF: ID {xdf_stream_id}, Name: {lsl_stream_info.name()}, LSL UID: {uid}, Format: {lsl_channel_format_str}")
        return xdf_stream_id

    def write_samples(self, stream_uid, samples, timestamps):
        if not self.file:
            raise IOError("File not open.")
        if stream_uid not in self.stream_info_map:
            print(f"Error: Stream UID {stream_uid} not found. Cannot write samples.")
            return

        stream_details = self.stream_info_map[stream_uid]
        xdf_stream_id = stream_details["xdf_stream_id"]
        num_channels = stream_details["lsl_info"].channel_count()
        struct_fmt_char = stream_details["struct_format_char"]
        lsl_format_str = stream_details["lsl_channel_format_str"]

        if not samples or not timestamps or len(samples) != len(timestamps):
            # print(f"Warning: No samples/timestamps or mismatch for stream {stream_uid}. Skipping.")
            return

        # Samples chunk content: [N=NumSampleBytes] [StreamID] ([M=NumBytesTimestamp] [Timestamp1] ... ) ([Value1] ... )
        # Actual XDF: [StreamID] then content, which is [N] (timestamps...) (samples...)
        # Our _write_chunk handles the StreamID prefixing for SAMPLES_TAG.
        # So, content starts with [N] (for string) or directly samples (for numeric)

        # Timestamps part: [M=num_bytes_for_ts] [ts1] [ts2] ...
        ts_payload = bytearray()
        ts_payload.append(8) # M = 8 bytes for double precision timestamps
        for ts in timestamps:
            ts_payload.extend(struct.pack("<d", ts)) # Little-endian double

        # Samples part
        sample_payload = bytearray()
        if lsl_format_str == "string":
            # N = 4 (bytes for length prefix of each string)
            sample_payload.append(4) 
            for s_list in samples: # samples is list of [string_value]
                s = s_list[0] if isinstance(s_list, (list, tuple)) and s_list else ""
                encoded_s = s.encode('utf-8')
                sample_payload.extend(struct.pack("<I", len(encoded_s))) # Length prefix (uint32)
                sample_payload.extend(encoded_s)
        elif struct_fmt_char: # Numeric types
            # N = 0 (numeric samples directly follow, no per-sample length prefix)
            sample_payload.append(0)
            pack_str = f"<{num_channels}{struct_fmt_char}" # e.g. "<8f" for 8 float32 channels
            for sample_tuple in samples:
                if len(sample_tuple) != num_channels:
                    print(f"Warning: Sample for stream {stream_uid} has {len(sample_tuple)} channels, expected {num_channels}. Skipping sample: {sample_tuple}")
                    continue
                try:
                    sample_payload.extend(struct.pack(pack_str, *sample_tuple))
                except struct.error as e:
                    print(f"Error packing sample for stream {stream_uid} with format '{pack_str}': {sample_tuple}. Error: {e}. Skipping chunk.")
                    return # Skip this whole chunk if one sample fails
        elif lsl_format_str == "undefined":
            print(f"Stream {stream_uid} has 'undefined' channel format. Cannot write samples.")
            return
        else:
            print(f"Stream {stream_uid} has no struct_fmt_char and is not string/undefined ('{lsl_format_str}'). Cannot write samples.")
            return
        
        chunk_content = ts_payload + sample_payload
        self._write_chunk(SAMPLES_TAG, chunk_content, stream_id=xdf_stream_id)

    def write_stream_footer(self, stream_uid):
        if not self.file:
            raise IOError("File not open.")
        if stream_uid not in self.stream_info_map:
            print(f"Error: Stream UID {stream_uid} not found. Cannot write footer.")
            return

        stream_details = self.stream_info_map[stream_uid]
        xdf_stream_id = stream_details["xdf_stream_id"]
        lsl_stream_info = stream_details["lsl_info"]
        lsl_channel_format_str = stream_details["lsl_channel_format_str"]

        root = ET.Element("info")
        ET.SubElement(root, "name").text = lsl_stream_info.name()
        ET.SubElement(root, "type").text = lsl_stream_info.type()
        ET.SubElement(root, "channel_count").text = str(lsl_stream_info.channel_count())
        ET.SubElement(root, "nominal_srate").text = str(lsl_stream_info.nominal_srate())
        ET.SubElement(root, "channel_format").text = lsl_channel_format_str
        ET.SubElement(root, "source_id").text = stream_uid # This should be stream_uid (LSL UID)

        # Optional: Add first_timestamp, last_timestamp, sample_count if tracked
        # ET.SubElement(root, "first_timestamp").text = str(stream_details.get("first_ts", 0))
        # ET.SubElement(root, "last_timestamp").text = str(stream_details.get("last_ts", 0))
        # ET.SubElement(root, "sample_count").text = str(stream_details.get("sample_count", 0))
        
        desc_outer = ET.SubElement(root, "desc")
        lsl_desc = lsl_stream_info.desc()
        if lsl_desc is not None:
            try:
                # Try to get the first child if it exists
                child = lsl_desc.first_child()
                if not child.empty():
                    while not child.empty():
                        el = ET.SubElement(desc_outer, child.name())
                        el.text = child.child_value()
                        sub_child = child.first_child()
                        while not sub_child.empty():
                            sub_el = ET.SubElement(el, sub_child.name())
                            sub_el.text = sub_child.child_value()
                            sub_child = sub_child.next_sibling()
                        child = child.next_sibling()
            except Exception as e:
                print(f"Warning: Could not process LSL description for stream {stream_uid} in footer: {e}")
                ET.SubElement(desc_outer, "source_format").text = "LSL_minimal_description"
        else:
            ET.SubElement(desc_outer, "source_format").text = "LSL_minimal_description"

        xml_content_string = ET.tostring(root, encoding="utf-8").decode('utf-8')
        self._write_chunk(STREAM_FOOTER_TAG, xml_content_string, stream_id=xdf_stream_id)
        print(f"Wrote StreamFooter for stream {stream_uid} (ID {xdf_stream_id})")

    def write_clock_offset(self, stream_id, time_val, offset_val):
        # stream_id here is XDF stream_id, though ClockOffset not always tied to one stream in XDF spec
        # For LSL, it's usually about remote clock vs local LSL clock, so perhaps stream_id = 0 (global)
        # or a specific stream_id if it's a per-stream offset measurement.
        # The XDF specification says <StreamID> is part of ClockOffset chunk content.
        if not self.file:
            raise IOError("File not open.")
        content = struct.pack("<dd", time_val, offset_val) # time (double), offset (double)
        # Pass the associated xdf_stream_id if this offset is for a particular stream's clock sync event
        # Or pass 0 if it's a general clock offset not tied to a specific stream in this writer's map
        self._write_chunk(CLOCK_OFFSET_TAG, content, stream_id=stream_id) # Use XDF stream_id
        # print(f"Wrote ClockOffset chunk for XDF StreamID {stream_id}: Time={time_val}, Offset={offset_val}")

    def write_boundary_chunk(self):
        if not self.file:
            raise IOError("File not open.")
        # Boundary chunk content is a UUID (16 bytes)
        # For simplicity, using a fixed dummy UUID. Real applications should generate unique UUIDs.
        #boundary_uuid = uuid.uuid4().bytes # Requires import uuid
        boundary_uuid_bytes = b'\x12\x34\x56\x78\x90\xab\xcd\xef\xfe\xdc\xba\x09\x87\x65\x43\x21'
        self._write_chunk(BOUNDARY_TAG, boundary_uuid_bytes, stream_id=0) # stream_id=0 as it's file-global
        print("Wrote Boundary chunk.")

    def close(self):
        if self.file:
            # Optionally write footers for all streams that were added
            # for uid in self.stream_info_map.keys():
            #     self.write_stream_footer(uid)
            self.file.close()
            self.file = None
            print(f"XDF file {self.filename} closed.")

# --- Mock StreamInfo for testing ---
class MockDesc:
    def __init__(self, children=None):
        self._children = children if children else []
        self._current_child_idx = -1

    def child_count(self):
        return len(self._children)

    def first_child(self):
        if not self._children:
            return MockEmptyDescElement()
        self._current_child_idx = 0
        return MockDescElement(self._children[0]["name"], self._children[0]["value"], self._children[0].get("children"))

class MockDescElement:
    def __init__(self, name, value, children_data=None):
        self._name = name
        self._value = value
        self._children_data = children_data if children_data else []
        self._parent_MocKDescElement = None # For next_sibling
        self._current_child_idx = -1 # For first_child/next_sibling of this element

    def name(self):
        return self._name

    def child_value(self):
        return self._value

    def empty(self):
        return False
    
    def first_child(self):
        if not self._children_data:
            return MockEmptyDescElement()
        self._current_child_idx = 0
        # This is a simplified mock, assuming children_data is a list of dicts like [{'name': ..., 'value': ...}]
        return MockDescElement(self._children_data[0]["name"], self._children_data[0]["value"])

    def next_sibling(self):
        # This part is tricky to mock perfectly without full context of the parent iterator
        # For this simple mock, assume it's handled by the caller's loop logic or needs a proper parent ref
        # Let's return an empty element to stop iteration in the mock scenario
        if self._parent_MocKDescElement and hasattr(self._parent_MocKDescElement, '_current_child_idx') and hasattr(self._parent_MocKDescElement, '_children'):
            self._parent_MocKDescElement._current_child_idx +=1
            if self._parent_MocKDescElement._current_child_idx < len(self._parent_MocKDescElement._children):
                 return MockDescElement(self._parent_MocKDescElement._children[self._parent_MocKDescElement._current_child_idx]["name"], self._parent_MocKDescElement._children[self._parent_MocKDescElement._current_child_idx]["value"],self._parent_MocKDescElement._children[self._parent_MocKDescElement._current_child_idx].get("children"))
        return MockEmptyDescElement() 

class MockEmptyDescElement:
    def empty(self):
        return True
    def name(self): return ""
    def child_value(self): return ""
    def first_child(self): return self
    def next_sibling(self): return self

class MockStreamInfo:
    def __init__(self, name, stype, channel_count, nominal_srate, channel_format, source_id, uid, desc_children=None):
        self._name = name
        self._type = stype
        self._channel_count = channel_count
        self._nominal_srate = nominal_srate
        self._channel_format = channel_format
        self._source_id = source_id
        self._uid = uid
        self._desc = MockDesc(desc_children)

    def name(self): return self._name
    def type(self): return self._type
    def channel_count(self): return self._channel_count
    def nominal_srate(self): return self._nominal_srate
    def channel_format(self): return self._channel_format
    def source_id(self): return self._source_id # LSL specific, XDF uses this as stream UID usually
    def uid(self): return self._uid # Actual LSL UID
    def desc(self): return self._desc

# Example usage (for testing the writer directly)
if __name__ == '__main__':
    writer = SimpleXDFWriter("test_output_corrected.xdf")
    writer.open()

    # Mock LSL Stream Info objects
    desc_eeg = [
        {"name": "manufacturer", "value": "FancyBCI"},
        {"name": "model", "value": "NeuroScan"},
        {
            "name": "channels", "value": "", 
            "children": [
                {"name": "channel", "value": "Cz"},
                {"name": "channel", "value": "Pz"}
            ]
        }
    ]
    eeg_info = MockStreamInfo("TestEEG", "EEG", 2, 100.0, cf_float32, "my_eeg_source_id", "eeg_uid_12345", desc_children=desc_eeg)
    marker_info = MockStreamInfo("TestMarkers", "Markers", 1, 0.0, cf_string, "my_marker_source_id", "marker_uid_67890")

    eeg_xdf_id = writer.add_stream(eeg_info)
    marker_xdf_id = writer.add_stream(marker_info)

    # Simulate receiving and writing some data
    eeg_samples = []
    eeg_timestamps = []
    for i in range(5):
        timestamp = time.time()
        sample = (np.random.rand(eeg_info.channel_count()) * 100).tolist()
        eeg_samples.append(sample)
        eeg_timestamps.append(timestamp)
        time.sleep(0.01)
    
    writer.write_samples(eeg_info.uid(), eeg_samples, eeg_timestamps)
    print(f"Wrote {len(eeg_samples)} EEG samples.")

    marker_samples = []
    marker_timestamps = []
    marker_events = ["MarkerA", "MarkerB", "MarkerC"]
    for i in range(3):
        timestamp = time.time()
        # String samples are expected as list of lists/tuples, e.g., [["MarkerA"]]
        marker_samples.append([marker_events[i]]) 
        marker_timestamps.append(timestamp)
        time.sleep(0.05)

    writer.write_samples(marker_info.uid(), marker_samples, marker_timestamps)
    print(f"Wrote {len(marker_samples)} Marker samples.")

    # Example ClockOffset (optional)
    # writer.write_clock_offset(eeg_xdf_id, time.time(), 0.001) # For EEG stream
    # writer.write_clock_offset(0, time.time(), -0.5) # Global/unassociated offset
    
    # Example Boundary Chunk (optional)
    # writer.write_boundary_chunk()

    # Write footers before closing (optional, but good practice for some readers)
    writer.write_stream_footer(eeg_info.uid())
    writer.write_stream_footer(marker_info.uid())

    writer.close()

    print("\nTo verify, load 'test_output_corrected.xdf' using an XDF reader (e.g., pyxdf or EEGLAB).")
    print("You can also use the verify_xdf.py script if you have it:")
    print("python verify_xdf.py --file test_output_corrected.xdf") 