import logging
import sys
import soc.omap4
import global_env

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        index = 0
        for arg in sys.argv[1:]:
            if arg == '-s':
                global_env.STEPPING = True
            elif arg == '-p':
                soc.omap4.TINYOS_PATH = sys.argv[index+2]
            index += 1
            
        
    except:
        pass
    main_thing =  soc.omap4.OMAP4()
    main_thing.boot()