import logging
from datetime import datetime

def getmylogger(name):
    time = datetime.now().strftime("%Y-%m-%d")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - module:%(module)s - function:%(module)s - %(message)s')
    
    file_handler = logging.FileHandler("error_logs/logfile-{}.log".format(str(time)))
    file_handler.setLevel(logging.WARN)
    file_handler.setFormatter(formatter)
    debug_log_handler = logging.FileHandler("debug_logs/logfile-{}.log".format(str(time)))
    debug_log_handler.setLevel(logging.DEBUG)
    debug_log_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(debug_log_handler)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    
    return logger