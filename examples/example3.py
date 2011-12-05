import logging

from controllers.memory import SimpleMemory, SimpleMMU
from buses.simple_bus import SimpleBus
from processor.execution_engine import SimpleEngine


logging.basicConfig(level=logging.INFO)

main_memory = SimpleMemory("simple_memory", 100, 'whatever')
mmu = SimpleMMU("simple_mmu")
bus = SimpleBus("simple_bus")

bus.attach_slave(mmu, 0, 100, 0)
mmu.attach_slave(main_memory, 0, 1000, 0)

main_memory.write(0, 1)
main_memory.write(4, 2)
main_memory.write(8, 3)

# Invalid so far.
main_memory.write(12, 4)

engine = SimpleEngine("simple_engine", bus)
engine.start()