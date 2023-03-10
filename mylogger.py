import logging
from datetime import datetime

def getmylogger(name):
    time = datetime.now().strftime("%Y-%m-%d")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - module:%(module)s - function:%(module)s - %(message)s')
    
    file_handler = logging.FileHandler("logs/logfile-{}.log".format(str(time)))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    
    return logger