import logging

from buses.simple_bus import SimpleBus
from controllers.timer import SimpleTimer, TIMER_IRQ, SimpleConsumer
from controllers.ic import SimpleInterruptController

logging.basicConfig(level=logging.INFO)

bus = SimpleBus("simple_bus")
timer = SimpleTimer("simple_timer")

bus.attach_to(timer, TIMER_IRQ, 5)
bus.attach_to(timer, TIMER_IRQ, 6)

ic = SimpleInterruptController("simple_ic")

ic.attach_to(bus, 5, 10)
ic.attach_to(bus, 6, 11)
ic.enable_all()
ic.mask_irq(10)

consumer = SimpleConsumer("simple_consumer")
consumer.attach_to(ic, 0, 6)

timer.start()