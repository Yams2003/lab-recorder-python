"""
XDF (Extensible Data Format) handling module

Provides XDF file writing and inspection capabilities.
"""

from .writer import SimpleXDFWriter
from .inspector import inspect_xdf_file

__all__ = ['SimpleXDFWriter', 'inspect_xdf_file'] 