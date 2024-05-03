import logging
import os
import sys

from loguru import logger
from uvicorn import Config, Server

from settings import settings

LOG_LEVEL = (
    logging.getLevelName("INFO")
    if not settings.DEBUG
    else logging.getLevelName("DEBUG")
)
JSON_LOGS = bool(os.environ.get("JSON_LOGS")) if not settings.JSON_LOGS else True


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _setup_logging():
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LOG_LEVEL)
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": JSON_LOGS}])


if __name__ == "__main__":
    server = Server(
        Config(
            "main:app",
            host=str(settings.HOST),
            log_level=LOG_LEVEL,
            port=settings.PORT,
            reload=settings.RELOAD,
        ),
    )
    _setup_logging()

    server.run()
