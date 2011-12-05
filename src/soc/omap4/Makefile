all: output.bin

output.bin:
	@arm-none-eabi-as rom.S -o rom.o
	@arm-none-eabi-objcopy -O binary rom.o rom.bin
	@arm-none-eabi-as ram_vecs.S -o ram_vecs.o
	@arm-none-eabi-objcopy -O binary ram_vecs.o ram_vecs.bin

clean:
	@rm rom.o rom.bin ram_vecs.o ram_vecs.bin

read: output.bin
	@arm-none-eabi-objdump -m arm -b binary -D rom.bin
	@arm-none-eabi-objdump -m arm -b binary -D ram_vecs.bin
