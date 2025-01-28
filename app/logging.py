import logging
import sys
from rich.console import Console
from rich.logging import RichHandler
from .config import settings

# Create console handler
console = Console(force_terminal=True)

# Configure Rich handler
rich_handler = RichHandler(
    console=console,
    rich_tracebacks=True,
    tracebacks_show_locals=settings.DEBUG,
    markup=True,
    show_time=True,
    show_path=False,  # Hide path for cleaner logs
)

# Configure Root logger
logging.basicConfig(
    level=settings.LOG_LEVEL,  # Use configured log level
    format="%(message)s",
    datefmt="[%X]",
    handlers=[rich_handler],
    force=True
)

# Get our application logger
logger = logging.getLogger("app")
logger.setLevel(settings.LOG_LEVEL)

# Configure module loggers with appropriate levels
loggers = {
    "uvicorn": "INFO",
    "fastapi": "INFO",
    "app.srl": "INFO",  # Set SRL module to INFO by default
}

# Apply configuration to all loggers
for name, level in loggers.items():
    _logger = logging.getLogger(name)
    _logger.handlers = [rich_handler]
    _logger.setLevel(level)
    _logger.propagate = False

# Ensure all uncaught exceptions are logged
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception 