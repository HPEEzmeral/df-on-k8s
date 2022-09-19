import os
from logging.handlers import RotatingFileHandler

"""
This log file handler will rotate the logfile (optionally) every time the
logging mechanism is initialized. This is different than the RotatingFileHandler
which will only rotate the log file when the maxBytes is set.
"""


# noinspection PyPep8Naming
class InstanceRotatingFileHandler(RotatingFileHandler):
    # WARNING: can't fix the warnings in this class because the call to this
    # constructor depends on the specific names not parameter order
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None, delay=0, rollover=True):

        log_filename_exists = os.path.exists(filename)

        # always 0 for this logger
        maxBytes = 0
        # always append for this logger
        mode = 'a'

        RotatingFileHandler.__init__(self, filename, mode, maxBytes, backupCount, encoding, delay)

        # do the rollover only if the file exists already otherwise you will
        # immedietely end up with two log files, one with nothing in it.
        if log_filename_exists and rollover:
            self.doRollover()
