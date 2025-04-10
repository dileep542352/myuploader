import time
import math
import os
from datetime import datetime, timedelta
from pyrogram.errors import FloodWait
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Timer:
    """A simple timer to enforce time intervals between actions."""
    def __init__(self, time_between=5):
        self.start_time = time.time()
        self.time_between = time_between

    def can_send(self):
        """Check if enough time has passed to allow an action."""
        if time.time() > (self.start_time + self.time_between):
            self.start_time = time.time()
            return True
        return False

    def reset(self):
        """Reset the timer to the current time."""
        self.start_time = time.time()

def hrb(value, digits=2, delim="", postfix=""):
    """Convert bytes to a human-readable file size (e.g., KiB, MiB)."""
    if value is None or value < 0:
        return "0 B"
    chosen_unit = "B"
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        if value >= 1024:
            value /= 1024
            chosen_unit = unit
        else:
            break
    return f"{value:.{digits}f}{delim}{chosen_unit}{postfix}"

def hrt(seconds, precision=0):
    """Convert seconds to a human-readable time string (e.g., 1d2h3m4s)."""
    if seconds < 0:
        return "0s"
    pieces = []
    value = timedelta(seconds=int(seconds))  # Ensure integer seconds

    if value.days:
        pieces.append(f"{value.days}d")

    seconds = value.seconds
    if seconds >= 3600:
        hours = seconds // 3600
        pieces.append(f"{hours}h")
        seconds %= 3600

    if seconds >= 60:
        minutes = seconds // 60
        pieces.append(f"{minutes}m")
        seconds %= 60

    if seconds > 0 or not pieces:
        pieces.append(f"{seconds}s")

    return "".join(pieces[:precision]) if precision else "".join(pieces)

timer = Timer()

async def progress_bar(current, total, reply, start, bar_length=11):
    """
    Display an upload progress bar with speed, percentage, and ETA.
    
    Args:
        current (int): Bytes uploaded so far.
        total (int): Total bytes to upload.
        reply: Pyrogram message object to edit.
        start (float): Start time of the upload.
        bar_length (int): Length of the progress bar in characters.
    """
    if not timer.can_send():
        return

    if total <= 0:  # Prevent division by zero
        logger.warning("Total size is zero or negative, skipping progress update.")
        return

    now = time.time()
    diff = now - start
    if diff < 1:  # Avoid premature updates
        return

    try:
        perc = min(100.0, current * 100 / total)  # Cap at 100%
        elapsed_time = round(diff)
        speed = current / elapsed_time if elapsed_time > 0 else 0
        remaining_bytes = total - current
        eta = hrt(remaining_bytes / speed, precision=1) if speed > 0 else "N/A"

        sp = hrb(speed) + "/s"
        tot = hrb(total)
        cur = hrb(current)

        completed_length = min(bar_length, int(perc * bar_length / 100))
        remaining_length = bar_length - completed_length
        progress_bar_str = "◆" * completed_length + "◇" * remaining_length

        message = (
            f"**╭──⌈📤 𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 📤⌋──╮**\n"
            f"┣⪼ [{progress_bar_str}]\n"
            f"┣⪼ 🚀 𝙎𝙥𝙚𝙚𝙙: {sp}\n"
            f"┣⪼ 📈 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨: {perc:.1f}%\n"
            f"┣⪼ ⏳ 𝙇𝙤𝙖𝙙𝙚𝙙: {cur}\n"
            f"┣⪼ 🍁 𝙎𝙞𝙯𝙚: {tot}\n"
            f"┣⪼ 🕛 𝙀𝙏𝘼: {eta}\n"
            f"╰────⌈ **✪ 𝐀𝐧𝐤𝐢𝐭 ✪** ⌋────╯"
        )

        retries = 3
        for attempt in range(retries):
            try:
                await reply.edit(message)
                break
            except FloodWait as e:
                logger.warning(f"FloodWait triggered, sleeping for {e.x} seconds.")
                time.sleep(e.x)
            except Exception as e:
                logger.error(f"Error updating progress: {e}")
                break
    except Exception as e:
        logger.error(f"Unexpected error in progress_bar: {e}")
        return

# Example usage (for testing)
if __name__ == "__main__":
    print(hrb(123456789, digits=2))  # Test human-readable bytes
    print(hrt(3665))  # Test human-readable time (1h1m5s)
