"""
Stream management module for Lab Recorder

Handles LSL stream discovery, selection, and data acquisition.
"""

from .manager import StreamManager
from .acquisition import AcquisitionThread, AcquisitionManager

__all__ = ['StreamManager', 'AcquisitionThread', 'AcquisitionManager'] 