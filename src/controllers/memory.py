from ctypes import c_uint32
import logging

from controllers.interfaces import AbstractBankedAddressableObject,\
    AbstractBankedAddressableObjectProxy
from controllers.exceptions.memory_exceptions import ReadOnlyMemory


class SimpleMemory(AbstractBankedAddressableObject):
    def __init__(self, name, memory_size, endiannes):
        AbstractBankedAddressableObject.__init__(self)
        self.logger = logging.getLogger(name)    
        self._size = memory_size * 1024
        self._serve_region(0, self._size)
        self._memory = (c_uint32 * self._size)()
        
    def _read(self, address):
        address = address & ~3
        value = self._memory[address]
        self.logger.info("Reading value (%s) from address (%s)", hex(value), hex(address))
        return c_uint32(value)
    
    def _write(self, address, value):
        self.logger.info("Writing value (%s) to address (%s)", hex(value.value), hex(address))
        address = address & ~3
        self._memory[address] = value.value


class SimpleROM(SimpleMemory):
    def __init__(self, name, memory_size, endiannes):
        SimpleMemory.__init__(self, name, memory_size, endiannes)
    
    def _write(self, address, value):
        raise ReadOnlyMemory(address)
    
    def _init_write(self, address, value):
        super(SimpleROM, self)._write(address, value)
        


class SimpleBankedMemory(AbstractBankedAddressableObject):
    def __init__(self, name, memory_size, endiannes):
        AbstractBankedAddressableObject.__init__(self)
        self.logger = logging.getLogger(name)    
        self._size = memory_size * 1024
        self._serve_region(0, self._size)
        self._memory = (c_uint32 * self._size)()
        
    def _read(self, address, bank=0):
        address = address & ~3
        value = self._memory[address]
        self.logger.info("Reading value (%s) from address (%s)", hex(value), hex(address))
        return c_uint32(value)
    
    def _write(self, address, value, bank=0):
        self.logger.info("Writing value (%s) to address (%s)", hex(value), hex(address))
        address = address & ~3
        self._memory[address] = value.value
        
class SimpleMMU(AbstractBankedAddressableObjectProxy):
    def __init__(self, name):
        AbstractBankedAddressableObjectProxy.__init__(self)
        self.logger = logging.getLogger(name)
        self.ttb = 0x0
        
    # Set translation table base.
    def set_ttb(self, address):
        self.ttb = address
        
    def resolve_address(self, vaddress):
        if self.translation_enabled:
            return self.raw_read(self.ttb + ((vaddress >> 10) & ~3))
        else:
            return vaddress