import os
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Define custom formatter with more details
class DetailedFormatter(logging.Formatter):
    """Custom formatter that includes exception traceback when available"""
    
    def formatException(self, exc_info):
        """Include full traceback for exceptions"""
        result = super().formatException(exc_info)
        return f"\n{result}"
    
    def format(self, record):
        """Enhanced format method with special handling for exceptions"""
        formatted = super().format(record)
        if record.exc_info:
            # Add separator line before exception info
            formatted += f"\n{'=' * 50}\n"
        return formatted

# Create formatters
console_formatter = DetailedFormatter(
    "%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S"
)

file_formatter = DetailedFormatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create handlers
# Main log file with rotation
main_handler = RotatingFileHandler(
    "logs/bot.log", 
    maxBytes=50000000,  # ~50MB
    backupCount=10
)
main_handler.setFormatter(file_formatter)
main_handler.setLevel(logging.INFO)

# Error log file specifically for errors
error_handler = RotatingFileHandler(
    "logs/error.log",
    maxBytes=20000000,  # ~20MB
    backupCount=5
)
error_handler.setFormatter(file_formatter)
error_handler.setLevel(logging.ERROR)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO)

# Debug log for detailed information during development
debug_handler = RotatingFileHandler(
    "logs/debug.log",
    maxBytes=30000000,  # ~30MB
    backupCount=3
)
debug_handler.setFormatter(file_formatter)
debug_handler.setLevel(logging.DEBUG)

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[main_handler, error_handler, console_handler, debug_handler]
)

# Set specific loggers to different levels
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

# Create our logger
logger = logging.getLogger(__name__)

# Add exception hook to catch and log unhandled exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions by logging them"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupts
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Helper function to log exceptions with full traceback
def log_exception(message, logger=logger):
    """Log an exception with the full traceback"""
    logger.error(f"{message}\n{traceback.format_exc()}")

# Custom logger methods for convenience
def log_start(message, logger=logger):
    """Log a process start with a distinctive format"""
    logger.info(f"▶️ STARTED: {message}")

def log_complete(message, logger=logger):
    """Log a process completion with a distinctive format"""
    logger.info(f"✅ COMPLETED: {message}")

def log_fail(message, logger=logger):
    """Log a process failure with a distinctive format"""
    logger.error(f"❌ FAILED: {message}")

logger.info("Logging system initialized")

# Export commonly used functions for importing in other modules
__all__ = ["logger", "log_exception", "log_start", "log_complete", "log_fail"]
