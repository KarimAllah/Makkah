import logging
import sys
import soc.omap4

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        soc.omap4.TINYOS_PATH = sys.argv[1]
    except:
        pass
    main_thing =  soc.omap4.OMAP4()
    main_thing.boot()