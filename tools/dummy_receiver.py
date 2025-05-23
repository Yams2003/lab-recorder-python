from pylsl import StreamInlet, resolve_streams

print("Looking for an EEG stream...")
streams_info_list = resolve_streams(2.0) # Timeout as positional

if not streams_info_list:
    print("No EEG streams found. Make sure send_dummy.py (or another LSL provider) is running.")
else:
    # Connect to the first found stream
    inlet = StreamInlet(streams_info_list[0])
    print(f"Connected to stream: {streams_info_list[0].name()} (UID: {streams_info_list[0].uid()})")
    print("Receiving data (press Ctrl+C to stop)...")

    try:
        while True:
            sample, timestamp = inlet.pull_sample(timeout=1.0)
            if timestamp:
                print(f"Timestamp: {timestamp:.4f}\tData: {sample}")
            else:
                print("No sample received in 1.0s")
    except KeyboardInterrupt:
        print("\nStream receiving stopped by user.")
    finally:
        if 'inlet' in locals() and inlet: # Make sure inlet was created
            inlet.close_stream()
        print("LSL connection closed.")
