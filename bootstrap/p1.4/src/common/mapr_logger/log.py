from __future__ import print_function

try:
    from StringIO import StringIO  # Python 2
except ImportError:
    from io import StringIO  # Python 3
import logging
import logging.config
import os
import stat
import sys
import traceback

import yaml


class LogException(Exception):
    def __init__(self, value):
        Exception.__init__(self, value)


class Log(object):
    CRITICAL = logging.CRITICAL
    FATAL = logging.FATAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARN
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    TRACE = 5
    NOTSET = logging.NOTSET

    # Needed to compare the name of this file to the method that iterates over
    # the call stack to get the correct calling method
    STACK_EXCLUDE = "common/mapr_logger/Log.py"
    NOT_INITIALIZED = "Log is not initialized: %s: %s"
    ALREADY_INITIALIZED = "The logger is already initialized."
    NO_CONFIGFILE = "A configuration file must be specified during log initialization."
    CONFIGFILE_NO_EXIST = "The configuration file specified at %s does not exist."
    NO_CONSOLE_LEVEL = "The console level must not be None."
    CONSOLE_LEVEL_INT = "The console level specified must be an integer or one of the predefined logger constants " \
                        "for example: logging.INFO."

    _log_filename = None
    _file_logger = None
    _console_logger = None
    _console_level = logging.NOTSET
    _warning_count = 0
    _error_count = 0

    @staticmethod
    def initialize(config_filename, log_filename, file_level=None, console_level=None, rollover=True):
        if Log._file_logger is not None:
            raise LogException(Log.ALREADY_INITIALIZED)

        # Check to make sure the configuration file exists because if you don't
        # you get a very obscure error:
        #     ConfigParser.NoSectionError: No section: 'formatters'
        if config_filename is None:
            raise LogException(Log.NO_CONFIGFILE)
        if not os.path.exists(config_filename):
            raise LogException(Log.CONFIGFILE_NO_EXIST % os.path.abspath(config_filename))

        with open(config_filename) as fp:
            logger_config = yaml.load(fp)

        # user might not override the level
        if file_level is not None:
            # set log level
            logger_config['logging']['handlers']['logFileHandler']['level'] = file_level
        if console_level is not None:
            # set log level
            logger_config['logging']['handlers']['consoleHandler']['level'] = console_level

        logger_config['logging']['handlers']['logFileHandler']['filename'] = log_filename
        logger_config['logging']['handlers']['logFileHandler']['rollover'] = rollover

        logging.addLevelName(Log.TRACE, "TRACE")
        logging.config.dictConfig(logger_config['logging'])

        Log._file_logger = logging.getLogger('fileLogger')
        Log._console_logger = logging.getLogger('consoleLogger')
        Log._log_filename = log_filename

    @staticmethod
    def get_log_filename():
        return Log._log_filename

    @staticmethod
    def get_console_level():
        if Log._console_logger is None or len(Log._console_logger.handlers) == 0:
            return logging.NOTSET

        return Log._console_logger.handlers[0].level

    @staticmethod
    def get_logfile_level():
        if Log._file_logger is None or len(Log._file_logger.handlers) == 0:
            return logging.NOTSET

        return Log._file_logger.handlers[0].level

    @staticmethod
    def close():
        logging.shutdown()
        Log._file_logger = None
        Log._console_logger = None
        Log._warning_count = 0
        Log._error_count = 0

        if Log._log_filename is not None:
            os.chmod(Log._log_filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

    @staticmethod
    def trace(msg, *args, **kwargs):
        Log._log(Log.TRACE, msg, args, **kwargs)

    @staticmethod
    def debug(msg, *args, **kwargs):
        Log._log(logging.DEBUG, msg, args, **kwargs)

    @staticmethod
    def info(msg, stdout=False, *args, **kwargs):
        if stdout:
            print(msg)
        Log._log(logging.INFO, msg, args, **kwargs)

    @staticmethod
    def warn(msg, update_count=True, *args, **kwargs):
        Log.warning(msg, update_count, *args, **kwargs)

    @staticmethod
    def warning(msg, update_count=True, *args, **kwargs):
        print("WARNING: {0}".format(msg))
        Log._log(logging.WARNING, msg, args, kwargs)
        if update_count:
            Log._warning_count += 1

    @staticmethod
    def error(msg, update_count=True, *args, **kwargs):
        print("ERROR: {0}".format(msg))
        Log._log(logging.ERROR, msg, args, kwargs)
        if update_count:
            Log._error_count += 1

    @staticmethod
    def critical(msg, update_count=True, *args, **kwargs):
        print("CRITICAL: {0}".format(msg))
        Log._log(logging.CRITICAL, msg, args, **kwargs)
        if update_count:
            Log._error_count += 1

    @staticmethod
    def exception(msg, update_count=True, *args, **kwargs):
        kwargs['exc_info'] = 1
        print("EXCEPTION: {0}".format(msg))
        Log._log(logging.ERROR, msg, args, **kwargs)
        if update_count:
            Log._error_count += 1

    @staticmethod
    def get_error_count():
        return Log._error_count

    @staticmethod
    def get_warning_count():
        return Log._warning_count

    @staticmethod
    def _find_caller():
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = Log._currentframe()
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename.endswith(Log.STACK_EXCLUDE):
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break
        return rv

    @staticmethod
    def _currentframe():
        """Return the frame object for the caller's stack frame."""
        # noinspection PyBroadException
        try:
            raise Exception
        except:
            return sys.exc_info()[2].tb_frame.f_back

    @staticmethod
    def _log(level, msg, args, exc_info=None, extra=None):
        if msg is None:
            return
        msg = str(msg).strip(' \n')

        if exc_info:
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()

        if Log._file_logger is None and Log._console_logger is None:
            if exc_info:
                sio = StringIO()
                traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=sio)
                s = sio.getvalue()
                sio.close()
                if s[-1:] == "\n":
                    s = s[:-1]
                print(Log.NOT_INITIALIZED % (logging.getLevelName(level), s))
            else:
                print(Log.NOT_INITIALIZED % (logging.getLevelName(level), msg))

        """Log the message to the logger(s)"""
        fn, lno, func = Log._find_caller()

        if Log._file_logger is not None:
            record = Log._file_logger.makeRecord(Log._file_logger.name, level,
                                                 fn, lno, msg, args, exc_info,
                                                 func, extra)
            Log._file_logger.handle(record)
