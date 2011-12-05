import logging
from soc.omap4 import OMAP4

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main_thing = OMAP4()
    main_thing.boot()
