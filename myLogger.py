import logging

logging.VERBOSE = 5


class MyHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        logging.addLevelName(logging.VERBOSE, "VERBOSE")
        formatter = logging.Formatter('%(filename)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)
