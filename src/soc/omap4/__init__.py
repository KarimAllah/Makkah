from controllers.interfaces import AbstractBankedAddressableObject
from host_frontends.binary_freader import BinaryFileReader
from controllers.memory import SimpleROM, SimpleMemory
from processors.arm.cortext_a9 import ARMCortexA9
from utils.string import convert_to_string
from buses.simple_bus import SimpleBus
from soc.omap4 import memory_map
from ctypes import c_uint32

import logging
import os

CUR_PATH        = os.path.dirname(os.path.abspath(__file__))
ROM_PATH        = os.path.join(CUR_PATH, "rom.o")
RAM_VECS_PATH   = os.path.join(CUR_PATH, "ram_vecs.o")
TINYOS_PATH     = "../examples/tinyos/output.bin"

class OMAP4(object):
    CHItems = ['CHSETTINGS', 'CHRAM', 'CHFLASH', 'CHMMCSD']
    
    def __init__(self):
        # Create a nand device "nand"
        self.sys_bus = SimpleBus('system bus')
        
        self.rom = SimpleROM("cortex-a9 mpu rom", 48, False)
        rom_file = BinaryFileReader(ROM_PATH)
        rom_file.readin(self.rom._init_write, 48 * 1024)
        rom_file.close()
        
        self.l3_ocm_ram = SimpleMemory("l3 ocm ram", 56, False)
        
        self.sys_bus.attach_slave(self.rom, memory_map.MPU_ROM_START, memory_map.MPU_ROM_END)
        self.sys_bus.attach_slave(self.l3_ocm_ram, memory_map.L3_OCM_RAM_START, memory_map.L3_OCM_RAM_END)
        
        self.mpu = CORTEXA9MPU('OMAP4 cortex-a9 mpu', self.sys_bus)
        
        
    def boot(self):
        self.mpu.boot()


class CORTEXA9MPU(object):
    def __init__(self, name, bus):
        self.cpu0 = ARMCortexA9('arm cortex a9', bus)
        self.bus = bus
        
    def boot(self):
#        nand_device = self.get_component("nand")
#        next = 0
#        data = nand_device.read(next, 512)
#        next = 512
#        
#        ch_found = False
#        for chitem in self.CHItems:
#            if chitem == convert_to_string(data, len(chitem)):
#                ch_found = True
#                break
#
#        if ch_found:
#            # Init ch stuff.
#            data = nand_device.read(next, 512)
#            next = 1024
#            
#        size = data[0]
#        dst = destination = data[1]
#
#        self.bus.write_chunk(destination, data, 510, 2)
#
#        size  = size - 512        
#        destination = destination + 510
#        data = nand_device.read(next, size)
#        self.bus.write_chunk(destination, data, size)
#        
#        # Branch to the beginning of the image.
#        some_address = 0 # Address of boot structure.
#        boot_parameters = (c_uint32 * 3)()
#        boot_parameters[0] = 0
#        boot_parameters[1] = 0x3 | (0 << 8) | (0 << 16)
#        
#        self.bus.write_chunk(some_address, boot_parameters, 3 * 4)
#         
#        self.cpu0.set_register('r0', some_address)
#        self.cpu0.set_ip(dst)

        ram_vecs_file = BinaryFileReader(RAM_VECS_PATH)
        ram_vecs_file.readin(self.bus.write, 56, memory_map.L3_OCM_RAM_EXCEPTIONS_VECTOR)
        ram_vecs_file.close()
        
        temp_os_file = BinaryFileReader(TINYOS_PATH)
        temp_os_file.readin(self.bus.write, temp_os_file.getsize(), memory_map.L3_OCM_RAM_START)
        
        self.cpu0.set_ip(c_uint32(memory_map.L3_OCM_RAM_START))
        self.cpu0.run()