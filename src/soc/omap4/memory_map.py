M  = 1024 * 1024

MPU_ROM_START                   = 0x40028000
MPU_ROM_END                     = 0x40033FFF

L3_OCM_RAM_START                = 0x40300000
L3_OCM_RAM_EXCEPTIONS_VECTOR    = 0x4030D000
L3_OCM_RAM_END                  = 0x4030DFFF

L4_CFG_DOMAIN_START             = 0x4A000000
L4_CFG_DOMAIN_END               = 0x4AFFFFFF

EMIF1_REGISTERS_START           = 0x4C000000
EMIF1_REGISTERS_END             = 0x4C000000 + (16*M)

EMIF2_REGISTERS_START           = 0x4D000000
EMIF2_REGISTERS_END             = 0x4D000000 + (16*M)

DMM_REGISTERS_START             = 0x4E000000
DMM_REGISTERS_END               = 0x4E000000 + (32*M)

LPDDR2_DRAM_START               = 0x80000000
LPDDR2_DRAM_END                 = 0x80000000 + (256*M)