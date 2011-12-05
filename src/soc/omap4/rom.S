# ROM exception vectors	( 0x40028000 => 0x40028020 )
# ROM CRC				( 0x40028020 => 0x40028080 )
# Dead loops			( 0x40028080 => 0x40028100 )
# Code					( 0x40028100 => 0x40028400 )
# API Table + Code		( 0x40028400 => 0x40033FFC )
# ROM Code version		( 0x40033FFC => 0x40033FFF )

.org 0x0
reset:
	ldr pc, rom_code

undefined:
	ldr pc, undefined_jmp

swi:
	ldr pc, swi_jmp

prefetch_abort:
	ldr pc, prefetch_abort_jmp

data_abort:
	ldr pc, data_abort_jmp

unused:
	ldr pc, unused_jmp

irq:
	ldr pc, irq_jmp

fiq:
	ldr pc, fiq_jmp

.org 0x20
rom_crc:

.org 0x80
dead_loops:

undefined_dl:
	b	.

swi_dl:
	b	.

.org 0x90
unused_dl:
	b	.

.org 0x98
fiq_dl:
	b	.


.org 0x100
rom_code:

undefined_jmp:
.long 0x4030D004

swi_jmp:
.long 0x4030D008

prefetch_abort_jmp:
.long 0x4030D00C

data_abort_jmp:
.long 0x4030D010

unused_jmp:
.long 0x4030D014

irq_jmp:
.long 0x4030D018

fiq_jmp:
.long 0x4030D01C

.org 0xbfff
