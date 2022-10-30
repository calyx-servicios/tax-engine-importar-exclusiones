"""Main script for Bot Job execution"""
import logging
import os
import sys

import debugpy
from bot import Bot

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
_logger = logging.getLogger(__name__)

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "false")
    debug_port = os.getenv("DEBUG_PORT", "3002")
    if debug == "true":
        _logger.info(f"====Starting Debugpy at {debug_port}===")
        debugpy.listen(("0.0.0.0", int(debug_port)))
        _logger.info("Wait for client....")
        debugpy.wait_for_client()
        debugpy.breakpoint()
        _logger.info("Debugging....")
    bot = Bot()
    bot.process()
