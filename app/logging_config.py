import sys
import os
import requests
from loguru import logger
from rich.logging import RichHandler
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Shared console for Rich
console = Console(force_terminal=True)

def setup_logging():
    """Configures Loguru to use Rich for high-fidelity terminal logging."""
    
    # 1. Clear existing handlers
    logger.remove()

    # 2. Add RichHandler Sink (The High-Fidelity Terminal View)
    logger.add(
        RichHandler(
            console=console,
            markup=True,
            rich_tracebacks=True,
            show_path=True,
            enable_link_path=True
        ),
        level=LOG_LEVEL,
        format="{message}",
        backtrace=True,
        diagnose=True
    )

    # 3. Intercept standard library logging
    import logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Force uvicorn/fastapi to use our interceptor
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        l = logging.getLogger(name)
        l.handlers = [InterceptHandler()]
        l.propagate = False

    logger.info(f"Loguru + [bold green]Rich[/bold green] initialized. Level: [cyan]{LOG_LEVEL}[/cyan]")
    return logger

# Initialize on import
setup_logging()
