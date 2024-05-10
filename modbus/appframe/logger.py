# https://docs.python.org/3/library/logging.html
# Level	Numeric value
# CRITICAL	50
# ERROR	    40
# WARNING	30
# INFO	    20
# DEBUG	    10
# NOTSET     0
#
# Mozno pouzit app_log NEBO primo v class BasicClient
# app_log.setLevel(DEBUG)

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.helpers import HelperOp

log_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s"
)

logFile = HelperOp.filename("control.log")
log_handler = RotatingFileHandler(
    logFile, mode="a", maxBytes=5 * 1024 * 1024, backupCount=2, encoding=None
)
log_handler.setFormatter(log_formatter)
app_log = logging.getLogger("apiframe")
app_log.addHandler(log_handler)
