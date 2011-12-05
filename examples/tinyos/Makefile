all: output.bin

output.bin: entry.S linker.ld
	@arm-none-eabi-as entry.S -o entry.o
	@arm-none-eabi-ld -z max-page-size=0x0 -T linker.ld entry.o -o output.elf
	@arm-none-eabi-objcopy -O binary output.elf output.bin

clean:
	@rm entry.o output.bin output.elf

read: output.bin
	@arm-none-eabi-objdump -m arm -b binary -D output.bin
