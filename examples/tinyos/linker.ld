OUTPUT_FORMAT("elf32-littlearm", "elf32-littlearm", "elf32-littlearm")
OUTPUT_ARCH("arm")
ENTRY(_start)

SECTIONS 
{
	. = 0x40300000;

	.text :
 	{
		*(.text)
	}

	.data :
	{
		*(.data)
	}

	.bss :
	{
		*(.bss)
	}

	.rodata :
	{
		*(.rodata .rodata.*)
	}

	/DISCARD/ :
	{
		*(*)
	}
}
