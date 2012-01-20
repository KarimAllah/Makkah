import sys
import time
import signal
import logging
import soc.omap4
import global_env
from gdb.gdbstub import GDBStubServer
from host_frontends.char_device import CharDevice

logger = logging.getLogger("Launcher")

def shutdown(signum, frame):
    logger.info("Received shutdown.")
    global_env.stop_all()

if __name__ == "__main__":
    logging.basicConfig(level=logging.CRITICAL)
    logging.addLevelName(logging.INFO, "\033[1;31m%s\033[1;m" % logging.getLevelName(logging.INFO))
    logging.addLevelName(logging.CRITICAL, "\033[1;41m%s\033[1;m" % logging.getLevelName(logging.CRITICAL))

    os_path = ""

    try:
        index = 0
        for arg in sys.argv[1:]:
            if arg == '-s':
                global_env.dbg_event.clear()
                global_env.STEPPING = True
            elif arg == '-p':
                os_path = sys.argv[index+2]
            elif arg == '-gdb':
                gdb_port = int(sys.argv[index+2])
            index += 1
    except:
        pass
    
    if not os_path:
        os_path = "../examples/tinyos/output.bin"
        logger.warning("Using default OS located at (%s)", os_path)

    soc.omap4.TINYOS_PATH = os_path

    if not gdb_port:
        logger.warning("Using default gdb port (20005)")
        gdb_port = 20005
    
    #signal.signal(signal.SIGINT, shutdown)
    #signal.signal(signal.SIGTERM, shutdown)
    main_thing =  soc.omap4.OMAP4()
    global_env.soc = main_thing
    main_thing.boot()
    time.sleep(0.5)
    
    char_dev = CharDevice(port=gdb_port)
    global_env.char_devices.append(char_dev)
    logger.critical("Waiting for gdb connection on port (%s)", gdb_port)
    char_dev.connect()
    gdb_server = GDBStubServer(char_dev)
    global_env.dbg = gdb_server
    gdb_server.start()
