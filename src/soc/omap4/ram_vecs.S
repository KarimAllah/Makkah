# RAM exception vectors ( 0x4030D000 => 0x4030D03C )

.org 0x4
undefined:
	ldr pc, undefined_addr

swi:
	ldr pc, swi_addr

prefetch_abort:
	ldr pc, prefetch_abort_addr

data_abort:
	ldr pc, data_abort_addr

unused:
	ldr pc, unused_addr

irq:
	ldr pc, irq_addr

fiq:
	ldr pc, fiq_addr

reserved_addr:
	.long 0x28090

undefined_addr:
	.long 0x28080

swi_addr:
	.long 0x28084

prefetch_abort_addr:
	.long 0x0

data_abort_addr:
	.long 0x0

unused_addr:
	.long 0x28090

irq_addr:
	.long 0x0

fiq_addr:
	.long 0x28098
