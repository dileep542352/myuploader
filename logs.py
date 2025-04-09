import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to see more logs
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("logs.txt", maxBytes=50000000, backupCount=10),
        logging.StreamHandler(),  # Outputs to console
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)  # Define logger here
