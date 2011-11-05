import logging

from buses.simple_bus import SimpleBus
from controllers.timer import SimpleTimer, TIMER_IRQ, SimpleConsumer
from controllers.ic import SimpleInterruptController

logging.basicConfig(level=logging.INFO)

bus = SimpleBus("simple_bus")
timer = SimpleTimer("simple_timer")

bus.attach_to(timer, TIMER_IRQ, 5)
timer.start()

consumer = SimpleConsumer("simple_consumer")

# Will cause the consumer's interrupt_triggered with IRQ '6' when IRQ '6' is raised in bus.
consumer.attach_to(bus, 5, 6)