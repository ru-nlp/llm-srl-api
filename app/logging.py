import logging
import sys
from rich.console import Console
from rich.logging import RichHandler
from .config import settings

def setup_rich_logging():
    """Initialize rich logging configuration for the application."""
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

    # Configure module loggers with appropriate levels
    loggers = {
        # External modules
        "uvicorn": "INFO",
        "fastapi": "INFO",
        
        # Application modules
        "app": settings.LOG_LEVEL,  # Root application logger
        "app.main": settings.LOG_LEVEL,  # Main application module
        "app.srl": settings.LOG_LEVEL,  # SRL module
        "app.srl.api": settings.LOG_LEVEL,  # SRL API endpoints
        "app.srl.analyzer": settings.LOG_LEVEL,  # SRL analyzer
    }

    # Apply configuration to all loggers
    for name, level in loggers.items():
        _logger = logging.getLogger(name)
        _logger.handlers = [rich_handler]
        _logger.setLevel(level)
        _logger.propagate = False  # Disable propagation for all loggers

    # Ensure all uncaught exceptions are logged
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        app_logger = logging.getLogger("app")  # Use root app logger for uncaught exceptions
        app_logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception 