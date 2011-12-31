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
        self.dmm_registers = SimpleMemory("dmm registers", 32 * 1024, False)
        self.emif1_registers = SimpleMemory("emif1 registers", 16 * 1024, False)
        self.emif2_registers = SimpleMemory("emif2 registers", 16 * 1024, False)
        
        self.l4_cfg_domain = SimpleMemory("l4 configuration domain", 16 * 1024, False)
        
        #rom
        self.sys_bus.attach_slave(self.rom, memory_map.MPU_ROM_START, memory_map.MPU_ROM_END)
        #ram
        self.sys_bus.attach_slave(self.l3_ocm_ram, memory_map.L3_OCM_RAM_START, memory_map.L3_OCM_RAM_END)
        #dmm
        self.sys_bus.attach_slave(self.dmm_registers, memory_map.DMM_REGISTERS_START, memory_map.DMM_REGISTERS_END)
        #emif1
        self.sys_bus.attach_slave(self.emif1_registers, memory_map.EMIF1_REGISTERS_START, memory_map.EMIF1_REGISTERS_END)
        #emif2
        self.sys_bus.attach_slave(self.emif2_registers, memory_map.EMIF2_REGISTERS_START, memory_map.EMIF2_REGISTERS_END)
        
        
        #FIXME: Set those properly.
        
        #l4_cfg domain
        self.sys_bus.attach_slave(self.l4_cfg_domain, memory_map.L4_CFG_DOMAIN_START, memory_map.L4_CFG_DOMAIN_END)
        
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
#        self.cpu0.set_register('r0', some_address)
#        self.cpu0.set_ip(dst)

        ram_vecs_file = BinaryFileReader(RAM_VECS_PATH)
        ram_vecs_file.readin(self.bus.write, 56, memory_map.L3_OCM_RAM_EXCEPTIONS_VECTOR)
        ram_vecs_file.close()
        
        temp_os_file = BinaryFileReader(TINYOS_PATH)
        os_size = temp_os_file.getsize()
        boot_struct_address = memory_map.L3_OCM_RAM_START + os_size
        temp_os_file.readin(self.bus.write, temp_os_file.getsize(), memory_map.L3_OCM_RAM_START)
        
        boot_parameters = []
        boot_parameters.append(c_uint32(0))
        boot_parameters.append(c_uint32(0))
        boot_parameters.append(c_uint32(0x3 | (0 << 8) | (0 << 16)))
        
        for index in range(3):
            self.bus.write(boot_struct_address + (index<<2), boot_parameters[index])
            
        
        self.cpu0.register_write(0, c_uint32(boot_struct_address))
        self.cpu0.set_ip(c_uint32(memory_map.L3_OCM_RAM_START))
        self.cpu0.run()