import time
import logging

from pipelines import transcoder

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(name="main")

while True:
    try:
        transcoder.run()
    except Exception as e:
        logger.error("Transcoder error: %s", repr(e))

    time.sleep(5)