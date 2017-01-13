"""
Logging
-------
Configure logging of messages
"""
# Standard
import os
from logging.config import dictConfig


def logging_init(level, logfile=None, debug_mode=False):
    """
    Given the log level and an optional logging file location, configure
    all logging.
    """
    # Get logging related arguments & the configure logging
    if logfile:
        logfile = os.path.abspath(logfile)

    # Don't bother with a file handler if we're not logging to a file
    handlers = ['console', 'filehandler'] if logfile else ['console', ]

    # If the main logging level is any of these, set librarys to WARNING
    lib_warn_levels = ('DEBUG', 'INFO', 'WARNING', )

    # The base logging configuration
    BASE_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            "ConsoleFormatter": {
                "format": "%(levelname)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "FileFormatter": {
                "format": ("%(levelname)-8s: %(asctime)s '%(message)s' "
                           "%(name)s:%(lineno)s"),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        'handlers': {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "ConsoleFormatter",
            },
        },
        'loggers': {
            'htmldiff': {
                'handlers': handlers,
                'level': level,
            },
        }
    }

    # If we have a log file, modify the dict to add in the filehandler conf
    if logfile:
        BASE_CONFIG['handlers']['filehandler'] = {
            'level': level,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logfile,
            'formatter': 'FileFormatter',
        }

    if debug_mode:
        BASE_CONFIG['handlers']['console']['formatter'] = 'FileFormatter'

    # Setup the loggers
    dictConfig(BASE_CONFIG)
