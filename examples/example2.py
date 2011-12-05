import logging

from controllers.memory import SimpleMemory, SimpleMMU
from buses.simple_bus import SimpleBus


logging.basicConfig(level=logging.INFO)

bus = SimpleBus("simple_bus")
main_memory = SimpleMemory("simple_memory", 100, 'whatever')
slave = SimpleMemory("slave_memory", 100, 'whatever', 4)

main_memory.attach_slave(slave, 100, 200, 0)
bus.attach_slave(main_memory, 0, 200, 0)

mmu = SimpleMMU("simple_mmu")
mmu.attach_slave(bus, 0, 1000, 0)


#mmu.write(100, 10000)
#mmu.read(100)
#
#mmu.write(100 * 1024 + 1000, 10000)
#mmu.read(100 * 1024 + 1000)
#
## Out of range.
#mmu.read(300 * 1024 + 1000)