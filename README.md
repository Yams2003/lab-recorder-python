# Lab Recorder Python

A Python implementation of a Lab Streaming Layer (LSL) recorder that saves multiple data streams to XDF files.

## What it does

Records data from LSL streams (EEG, markers, etc.) to XDF files with proper synchronization. Includes remote control via TCP commands for integration with experiments.

## Installation

```bash
git clone https://github.com/your-username/lab-recorder-python.git
cd lab-recorder-python

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### Simple recording

Start recording from all available streams:

```bash
python main.py -f my_recording.xdf
```

The recorder will:
1. Find all LSL streams on the network
2. Select all of them for recording  
3. Start recording immediately
4. Save to `my_recording.xdf`

Stop with Ctrl+C.

### With remote control

```bash
# Start recorder with remote control enabled
python main.py -f experiment.xdf

# In another terminal, control the recording
python tools/remote_client.py start
python tools/remote_client.py stop
```

### Testing with dummy data

```bash
# Terminal 1: Start test streams
python tools/send_dummy.py

# Terminal 2: Record the test data  
python main.py -f test.xdf

# Terminal 3: Verify the recording
python tools/inspect_xdf.py test.xdf
```

## Remote Control Commands

Connect to `localhost:22345` and send these commands:

- `status` - Get current recorder state
- `streams` - List available streams
- `start` - Begin recording
- `stop` - Stop recording  
- `select all` - Select all streams
- `filename newname.xdf` - Change output file

## File Structure

```
├── main.py                 # Main application entry point
├── labrecorder/           # Core recorder modules
│   ├── recorder.py        # Main recorder class
│   ├── streams/           # Stream management
│   ├── xdf/              # XDF file writing
│   ├── remote_control/   # TCP remote control
│   └── utils/            # Configuration and utilities
└── tools/                # Testing and utility scripts
    ├── streamer.py       # Generate test LSL streams
    ├── tester.py         # Verify recordings (pyxdf)
    ├── alternative_tester.py # Verify recordings (custom)
    ├── inspect_xdf.py    # Examine XDF files
    └── remote_client.py  # Command-line remote control
```

## Command Line Options

```bash
python main.py [options]

Options:
  -f, --filename FILE     Output XDF filename (default: recording.xdf)
  -p, --port PORT        Remote control port (default: 22345)
  --no-remote           Disable remote control
  --config FILE         Use configuration file
```

## Troubleshooting

**No streams found**: Check that LSL streams are running on your network. Test with `python tools/streamer.py`.

**Port already in use**: Stop other recorder instances with `./cleanup.sh` or kill processes using port 22345.

**Recording issues**: Check that you have write permissions in the output directory and enough disk space.

**Cross-compatibility issues**: If pyxdf can't read your files, use `python tools/inspect_xdf.py filename.xdf` to verify the recording and `python tools/alternative_tester.py filename.xdf` for validation.

## Requirements

- Python 3.8+
- pylsl (Lab Streaming Layer)
- numpy
- pyxdf (for file verification)


