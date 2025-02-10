# utils/logger.py
import logging
import datetime

def setup_logger():
    logging.basicConfig(
        filename=f"data/logs/{datetime.datetime.now().strftime('%Y-%m-%d')}.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger()