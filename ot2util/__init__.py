"""This module allows for more efficient organization and orchestration of Opentrons OT2 robots.
"""

__version__ = "0.0.1a1"

import logging
from time import gmtime

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s.%(msecs)03dZ|%(process)d|%(thread)d|%(levelname)s|%(name)s:%(lineno)s| %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
)

logging.Formatter.converter = gmtime
logger = logging.getLogger("ot2util")
logger.setLevel("DEBUG")
logger.addHandler(handler)
