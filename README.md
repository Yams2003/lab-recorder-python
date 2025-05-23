# Lab Recorder Python

A modern, cross-platform Python implementation of the Lab Streaming Layer (LSL) recorder with advanced remote control capabilities.

## 🔥 Key Features

- **Record multiple LSL streams simultaneously** with precise timestamp synchronization
- **Cross-platform support** - works on Windows, macOS, and Linux
- **XDF file format** - industry-standard format compatible with all LSL tools
- **TCP remote control** - control recording via network commands and JSON API
- **Multi-threaded data acquisition** - concurrent recording for optimal performance
- **Stream selection** - choose which streams to record with fine-grained control
- **Error recovery** - automatic stream reconnection and robust error handling
- **Modular architecture** - clean, extensible Python codebase
- **Comprehensive testing tools** - dummy data generators for development
- **Process management** - built-in cleanup scripts for development workflow

## 🏗️ Architecture Overview

### Component Structure
```
Lab Recorder Python Architecture
├── Main Application (main.py)
│   └── Command-line interface and entry point
├── Core Recorder (labrecorder/recorder.py)
│   ├── Session management and coordination
│   ├── Stream lifecycle management
│   └── Recording state control
├── Stream Management (labrecorder/streams/)
│   ├── manager.py: Stream discovery and selection
│   └── acquisition.py: Multi-threaded data capture
├── XDF File System (labrecorder/xdf/)
│   ├── writer.py: Real-time XDF file writing
│   └── inspector.py: File analysis and validation
├── Remote Control (labrecorder/remote_control/)
│   ├── server.py: TCP server with JSON protocol
│   ├── client.py: Client connection management
│   └── commands.py: Command parsing and execution
├── Utilities (labrecorder/utils/)
│   └── config.py: Configuration management
└── Development Tools (tools/)
    ├── dummy_sender.py: Test data generation
    ├── dummy_receiver.py: Test data consumption
    ├── remote_client.py: Command-line remote client
    └── inspect_xdf.py: XDF file analysis
```

### Data Flow
1. **Stream Discovery**: LSL network scan identifies available streams
2. **Stream Selection**: User/API selects which streams to record
3. **Inlet Creation**: LSL inlets established for each selected stream
4. **XDF Initialization**: Output file created with stream metadata
5. **Multi-threaded Capture**: Separate threads pull data from each stream
6. **Real-time Writing**: Data continuously written to XDF file
7. **Synchronization**: Clock offsets calculated and applied
8. **Remote Monitoring**: Status available via TCP interface

## 📋 System Requirements

### Python Environment
- **Python Version**: 3.8+ (3.9+ recommended)
- **Operating Systems**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Memory**: 512MB RAM minimum (2GB+ recommended for large streams)
- **Storage**: 1GB+ free space (depends on recording duration)

### Network Requirements
- **LSL Network**: Multicast-enabled network for stream discovery
- **TCP Port**: Default port 22345 for remote control (configurable)
- **Firewall**: Allow Python applications through firewall

### Dependencies
- **pylsl**: Lab Streaming Layer Python bindings
- **numpy**: Numerical computations and data handling
- **Standard Library**: threading, socket, json, struct, argparse

## 🚀 Installation & Setup

### Method 1: Quick Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/lab-recorder-python.git
cd lab-recorder-python

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate

# Install in development mode
pip install -e .
```

### Method 2: Direct Dependencies

```bash
# Install required packages
pip install pylsl numpy

# Make cleanup script executable (macOS/Linux)
chmod +x cleanup.sh
```

### Method 3: From Requirements File

```bash
# Install from requirements file
pip install -r requirements.txt
```

### Verification

```bash
# Test installation
python main.py --help

# Test LSL functionality
python tools/dummy_sender.py &
python main.py -f test_recording.xdf
```

## 🎯 Quick Start Guide

### 1. Basic Recording Session

```bash
# Terminal 1: Start test data streams
python tools/dummy_sender.py

# Terminal 2: Start recording
python main.py -f my_experiment.xdf

# Terminal 3: Control recording remotely
python tools/remote_client.py status
python tools/remote_client.py start
# ... let it record for desired duration ...
python tools/remote_client.py stop
```

### 2. Programmatic Control

```python
from labrecorder import LabRecorder

# Create recorder instance
recorder = LabRecorder(
    filename="experiment_001.xdf",
    enable_remote_control=True,
    remote_control_port=22345
)

# Discover and select streams
recorder.update_streams()
streams = recorder.get_available_streams()

# Select all streams (or filter by name/type)
stream_uids = [s.uid() for s in streams]
recorder.select_streams_to_record(stream_uids)

# Start recording
recorder.start_recording()

# Recording runs in background...
# Use remote control or wait for manual stop

# Stop and cleanup
recorder.stop_recording()
recorder.cleanup()
```

## 📖 Detailed Usage

### Command Line Interface

```bash
# Basic usage
python main.py [OPTIONS]

# Common options
python main.py -f output.xdf              # Specify output filename
python main.py --no-remote                # Disable remote control
python main.py -p 12345                   # Custom remote control port
python main.py --config config.json       # Use configuration file
python main.py --streams "EEG,EMG"        # Pre-select streams by name
python main.py --timeout 10               # Stream discovery timeout
```

### Remote Control Protocol

The remote control interface uses a simple text-based protocol over TCP:

#### Connection
```bash
# Using telnet
telnet localhost 22345

# Using netcat
nc localhost 22345

# Using the provided client
python tools/remote_client.py <command>
```

#### Available Commands

| Command | Parameters | Description | Example |
|---------|------------|-------------|---------|
| `status` | None | Get recorder status | `status` |
| `streams` | None | List available streams | `streams` |
| `update` | None | Refresh stream list | `update` |
| `select` | `all\|none\|<uid>` | Select streams for recording | `select all` |
| `start` | None | Begin recording | `start` |
| `stop` | None | Stop recording | `stop` |
| `filename` | `<filename>` | Set output filename | `filename exp1.xdf` |
| `get_filename` | None | Get current filename | `get_filename` |

#### Advanced Filename Templating

```bash
# Template with metadata
filename {root:/data/experiments} {template:sub-{participant}_ses-{session}_task-{task}.xdf} {participant:001} {session:baseline} {task:restingstate}

# Results in: /data/experiments/sub-001_ses-baseline_task-restingstate.xdf
```

### Configuration Management

Create a `config.json` file for persistent settings:

```json
{
  "recording": {
    "filename": "default_recording.xdf",
    "auto_start": false,
    "buffer_size": 360,
    "max_samples_per_pull": 500,
    "clock_sync_interval": 5.0
  },
  "remote_control": {
    "enabled": true,
    "port": 22345,
    "bind_address": "localhost"
  },
  "streams": {
    "discovery_timeout": 2.0,
    "auto_recover": true,
    "required_streams": ["EEG", "EMG"],
    "exclude_streams": ["Debug"]
  },
  "logging": {
    "level": "INFO",
    "file": "labrecorder.log",
    "console": true
  }
}
```

### Stream Selection Strategies

```python
# Select all available streams
recorder.select_streams_to_record([s.uid() for s in streams])

# Select by stream name
eeg_streams = [s for s in streams if "EEG" in s.name()]
recorder.select_streams_to_record([s.uid() for s in eeg_streams])

# Select by stream type
marker_streams = [s for s in streams if s.type() == "Markers"]
recorder.select_streams_to_record([s.uid() for s in marker_streams])

# Select by source hostname
local_streams = [s for s in streams if s.hostname() == "localhost"]
recorder.select_streams_to_record([s.uid() for s in local_streams])
```

## 🔧 Development & Testing

### Testing with Dummy Data

The application includes comprehensive testing tools:

```bash
# Start dummy data sender (creates 3 test streams)
python tools/dummy_sender.py

# Start dummy data receiver (for testing LSL network)
python tools/dummy_receiver.py

# Test recording with dummy data
python main.py -f test.xdf

# Inspect recorded files
python tools/inspect_xdf.py test.xdf
```

### Dummy Stream Specifications

- **DummyEEG**: 8-channel float32 EEG data at 250 Hz
- **DummyMarkers**: String markers with timestamps
- **DummyInt**: Integer sensor data at 100 Hz

### Process Management

During development, you may accumulate background processes:

```bash
# Clean up all Lab Recorder processes
./cleanup.sh

# Manual cleanup if needed
ps aux | grep "dummy_sender\|main.py" | grep -v grep
kill -9 <PID>
```

### Custom Stream Creation

```python
import pylsl

# Create a custom test stream
info = pylsl.StreamInfo(
    name="MyTestStream",
    type="EEG", 
    channel_count=4,
    nominal_srate=500,
    channel_format=pylsl.cf_float32,
    source_id="test123"
)

# Add channel metadata
channels = info.desc().append_child("channels")
for i in range(4):
    ch = channels.append_child("channel")
    ch.append_child_value("label", f"Ch{i+1}")
    ch.append_child_value("unit", "microvolts")
    ch.append_child_value("type", "EEG")

# Create outlet and send data
outlet = pylsl.StreamOutlet(info)
```

## 🎛️ Advanced Configuration

### Performance Tuning

```json
{
  "performance": {
    "buffer_size": 360,           // Seconds of data to buffer
    "max_samples_per_pull": 500,  // Max samples per acquisition cycle
    "writer_thread_priority": 1,  // Thread priority for file writing
    "acquisition_threads": "auto" // Number of acquisition threads
  }
}
```

### Network Configuration

```json
{
  "network": {
    "multicast_address": "224.0.0.183",
    "multicast_port": 16571,
    "unicast_port_range": [16572, 16604],
    "connection_timeout": 5.0,
    "max_buffer_length": 360
  }
}
```

### File System Options

```json
{
  "file_system": {
    "compression": "none",        // XDF compression level
    "flush_interval": 1.0,        // Disk flush frequency (seconds)
    "temp_directory": "/tmp",     // Temporary file location
    "backup_on_overwrite": true   // Create .bak files
  }
}
```

## 🐛 Troubleshooting

### Common Issues

#### "No streams found"
```bash
# Check LSL network connectivity
python -c "import pylsl; print(pylsl.resolve_streams(timeout=5))"

# Verify dummy sender is running
python tools/dummy_sender.py &
python -c "import pylsl; print(len(pylsl.resolve_streams()))"
```

#### "Address already in use" (Port 22345)
```bash
# Clean up processes
./cleanup.sh

# Or find and kill manually
lsof -ti tcp:22345 | xargs kill -9
```

#### "Permission denied" on cleanup.sh
```bash
# Make script executable
chmod +x cleanup.sh
```

#### High memory usage
- Reduce `buffer_size` in configuration
- Lower `max_samples_per_pull`
- Check for stream disconnections causing buffer buildup

#### Slow recording performance
- Use SSD storage for XDF files
- Increase `writer_thread_priority`
- Reduce number of concurrent streams
- Check network bandwidth for remote streams

### Debug Mode

```bash
# Enable verbose logging
python main.py -f debug.xdf --log-level DEBUG

# Check specific component logs
tail -f labrecorder.log | grep "StreamManager"
```

### Network Diagnostics

```bash
# Test LSL multicast
python -c "
import pylsl
import time
print('Discovering streams...')
streams = pylsl.resolve_streams(timeout=10)
print(f'Found {len(streams)} streams')
for s in streams:
    print(f'  {s.name()} ({s.type()}) from {s.hostname()}')
"
```

## 📊 Performance Benchmarks

### Typical Performance (on modern hardware)

| Scenario | Streams | Sample Rate | Channels | CPU Usage | Memory |
|----------|---------|-------------|----------|-----------|--------|
| Light EEG | 1 | 250 Hz | 8 | <5% | ~50MB |
| Multi-modal | 5 | 1000 Hz | 32 | ~15% | ~200MB |
| High-density | 10 | 2000 Hz | 128 | ~30% | ~500MB |

### Optimization Tips

1. **Use local streams when possible** - network latency affects performance
2. **Configure appropriate buffer sizes** - balance memory vs. data safety
3. **Use SSD storage** - faster disk writes improve overall performance
4. **Monitor system resources** - watch CPU, memory, and disk usage
5. **Regular cleanup** - use cleanup script during development

## 🔗 Integration Examples

### MATLAB Integration

```matlab
% Start recording from MATLAB
system('python main.py -f matlab_experiment.xdf &');
pause(2); % Wait for startup

% Send remote commands
tcp_client = tcpclient('localhost', 22345);
write(tcp_client, 'start');
response = read(tcp_client);

% Your experiment code here
pause(60); % Record for 60 seconds

% Stop recording
write(tcp_client, 'stop');
clear tcp_client;
```

### PsychoPy Integration

```python
from psychopy import core
import socket

# Connect to Lab Recorder
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 22345))

def send_command(command):
    sock.send(command.encode() + b'\n')
    return sock.recv(1024).decode()

# Start recording before experiment
send_command('start')

# Run your PsychoPy experiment
# ... experiment code ...

# Stop recording after experiment
send_command('stop')
sock.close()
```

### Unity Integration

```csharp
using System.Net.Sockets;
using System.Text;

public class LabRecorderController : MonoBehaviour {
    private TcpClient client;
    private NetworkStream stream;
    
    void Start() {
        client = new TcpClient("localhost", 22345);
        stream = client.GetStream();
        
        // Start recording when game starts
        SendCommand("start");
    }
    
    void SendCommand(string command) {
        byte[] data = Encoding.UTF8.GetBytes(command + "\n");
        stream.Write(data, 0, data.Length);
    }
    
    void OnApplicationQuit() {
        SendCommand("stop");
        stream.Close();
        client.Close();
    }
}
```

## 📝 File Format Details

### XDF Structure
The application generates standard XDF files with the following structure:

```
XDF File Structure:
├── FileHeader
│   ├── Magic number: "XDF:"
│   ├── Format version
│   └── Creation timestamp
├── StreamHeader (for each stream)
│   ├── Stream ID and metadata
│   ├── Channel information
│   └── Acquisition parameters
├── ClockOffset chunks
│   ├── Synchronization data
│   └── Clock drift compensation
├── Sample chunks
│   ├── Timestamped data samples
│   └── Stream-specific formatting
└── StreamFooter
    ├── Last timestamp
    └── Final sample count
```

### Metadata Preservation
- Original LSL stream metadata maintained
- Channel labels and units preserved
- Source application information included
- Network and timing information recorded

## 🤝 Contributing

### Development Setup

```bash
# Fork and clone repository
git clone https://github.com/your-username/lab-recorder-python.git
cd lab-recorder-python

# Create development environment
python -m venv dev-env
source dev-env/bin/activate  # or dev-env\Scripts\activate on Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black labrecorder/ tools/ main.py

# Check style
flake8 labrecorder/ tools/ main.py
```

## 🙏 Acknowledgments

- **Lab Streaming Layer (LSL)**: Core streaming protocol and libraries
- **XDF Format**: Standard file format for multi-stream recordings
- **LSL Community**: Tools, documentation, and support
- **Contributors**: All developers who have contributed to this project

## 📚 Additional Resources

- [LSL Documentation](https://labstreaminglayer.readthedocs.io/)
- [XDF Format Specification](https://github.com/sccn/xdf/wiki/Specifications)
- [PyLSL Documentation](https://pylsl.readthedocs.io/)
- [Lab Recorder (C++)](https://github.com/labstreaminglayer/App-LabRecorder)


