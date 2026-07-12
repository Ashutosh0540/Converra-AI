from pathlib import Path

from loguru import logger

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Remove default logger
logger.remove()

# Console logging
logger.add(
    sink=lambda msg: print(msg, end=""),
    level="INFO",
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
           "<level>{message}</level>",
)

# File logging
logger.add(
    "logs/converra.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
)

app_logger = logger