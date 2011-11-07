import ctypes
import struct
import logging

from controllers.interfaces import AbstractAddressableObject

class SimpleMemory(AbstractAddressableObject):
    def __init__(self, name, memory_size, endiannes, word_size):
        AbstractAddressableObject.__init__(self)
        
        self._size = memory_size * 1024
        self._serve_region(0, memory_size)
        self._struct = struct.Struct("I")
        self._memory = ctypes.create_string_buffer(self._size)
        self.logger = logging.getLogger(name)
        
    def _read(self, address):
        address = address & ~3
        value = self._struct.unpack_from(self._memory, address)[0]
        self.logger.info("Reading value (%s) from address (%s)", value, address)
        return value
    
    def _write(self, address, value):
        self.logger.info("Writing value (%s) to address (%s)", value, address)
        address = address & ~3
        self._struct.pack_into(self._memory, address, value)