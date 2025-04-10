import os
import time
import math
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures

from pyrogram import Client, filters
from pyrogram.types import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Global variables
failed_counter = 0

def duration(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)
    
def exec(cmd):
    process = subprocess.run(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output = process.stdout.decode()
    print(output)
    return output

def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        fut = executor.map(exec,cmds)

async def aio(url, name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return k

async def download(url, name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka

def parse_vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = []
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except:
                pass
    return new_info

def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.update({f'{i[2]}':f'{i[0]}'})
            except:
                pass
    return new_info

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode == 1:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'

def old_download(url, file_name, chunk_size = 1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"

def TimeFormatter(milliseconds: int) -> str:
    """Format time from milliseconds to string representation"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "") + \
          ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

async def progress_bar(current, total, message, start_time):
    """
    Progress bar function compatible with both implementations
    """
    now = time.time()
    diff = now - start_time
    if round(diff % 10) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(elapsed_time)
        estimated_total_time = TimeFormatter(estimated_total_time)

        progress = "[{0}{1}] \n**Progress**: {2}%\n".format(
            ''.join(["●" for _ in range(math.floor(percentage / 5))]),
            ''.join(["○" for _ in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "**Done**: {0} of {1}\n**Speed**: {2}/s\n**ETA**: {3}\n".format(
            human_readable_size(current),
            human_readable_size(total),
            human_readable_size(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(text=f"{tmp}")
        except:
            pass

async def progress_callback(current, total, message):
    """
    Progress callback function compatible with main.py
    """
    try:
        if not hasattr(message, 'start_time'):
            message.start_time = time.time()
            
        percentage = (current / total) * 100
        progress_bar = "♦" * int(percentage // 10) + "◇" * (10 - int(percentage // 10))
        speed = current / (time.time() - message.start_time) if time.time() > message.start_time else 0
        eta = (total - current) / speed if speed > 0 else 0
        text = (
            f"**__Uploading...__**\n"
            f"{progress_bar}\n"
            f"Progress: {percentage:.2f}%\n"
            f"Done: {human_readable_size(current)} / {human_readable_size(total)}\n"
            f"Speed: {human_readable_size(speed)}/s\n"
            f"ETA: {int(eta)}s"
        )
        await message.edit(text)
    except Exception as e:
        logging.error(f"Error in progress callback: {e}")

async def extract_stream_url(url):
    """
    Extract streaming URL from platform-specific pages
    """
    if "visionias" in url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36'
                }) as resp:
                    text = await resp.text()
                    import re
                    match = re.search(r"(https://.*?playlist.m3u8.*?)\"", text)
                    if match:
                        return match.group(1)
        except Exception as e:
            logging.error(f"Error extracting visionias URL: {e}")
            
    elif "classplusapp" in url:
        try:
            response = requests.get(
                f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', 
                headers={
                    'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'
                }
            )
            if response.status_code == 200:
                return response.json()['url']
        except Exception as e:
            logging.error(f"Error processing classplus URL: {e}")
            
    return url  # Return original if extraction fails

async def process_special_url(url, token=None):
    """
    Process special URL types as seen in main.py
    """
    if "master.mpd" in url:
        vid_id = url.split("/")[-2]
        return f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={token or 'unknown'}"
        
    elif "workers.dev" in url and "cloudfront.net/" in url:
        parts = url.split("cloudfront.net/")
        if len(parts) > 1:
            vid_id = parts[1].split("/")[0]
            return f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={token or 'unknown'}"
            
    elif "onlineagriculture" in url:
        parts = url.split("/")
        if len(parts) >= 4:
            vid_id, hls, quality, master = parts[-4], parts[-3], parts[-2], parts[-1]
            return f"https://appx-transcoded-videos.akamai.net.in/videos/onlineagriculture-data/{vid_id}/{hls}/720p/{master}"
            
    elif "livelearn.in" in url or "englishjaisir" in url:
        parts = url.split("/")
        if len(parts) >= 4:
            vid_id, hls, quality, master = parts[-4], parts[-3], parts[-2], parts[-1]
            return f"https://appx-transcoded-videos.livelearn.in/videos/englishjaisir-data/{vid_id}/{hls}/720p/{master}"
            
    elif "psitoffers.store" in url:
        parts = url.split("vid=")
        if len(parts) > 1:
            vid_id = parts[1].split("&")[0]
            return f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={token or 'unknown'}"
            
    # Return original URL if no special handling needed
    return url

async def download_video(url, cmd, name):
    """
    Enhanced video download function with platform-specific handling and retry logic
    """
    global failed_counter
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
    
    logging.info(f"Executing download command: {download_cmd}")
    k = subprocess.run(download_cmd, shell=True)
    
    # Platform-specific handling with retry logic
    if k.returncode != 0:
        if "visionias" in cmd and failed_counter <= 10:
            failed_counter += 1
            logging.warning(f"VisionIAS download failed, retrying ({failed_counter}/10)...")
            await asyncio.sleep(5)
            return await download_video(url, cmd, name)
        elif "penpencilvod" in cmd and failed_counter <= 10:
            failed_counter += 1
            logging.warning(f"PenPencil download failed, retrying ({failed_counter}/10)...")
            await asyncio.sleep(5)
            return await download_video(url, cmd, name)
        elif "cloudfront" in url and failed_counter <= 15:
            failed_counter += 1
            logging.warning(f"CloudFront download failed, retrying ({failed_counter}/15)...")
            await asyncio.sleep(3)
            return await download_video(url, cmd, name)
    
    # Reset counter on success
    failed_counter = 0
    
    # Check for output file with different possible extensions
    try:
        if os.path.isfile(name):
            return name
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"
            
        name_without_ext = name.split(".")[0]
        for ext in [".mkv", ".mp4", ".webm", ".mp4.webm"]:
            if os.path.isfile(f"{name_without_ext}{ext}"):
                return f"{name_without_ext}{ext}"
                
        logging.error(f"Could not find downloaded file for {name}")
        return name  # Return original name as fallback
    except Exception as e:
        logging.error(f"Error locating downloaded file: {str(e)}")
        return name

async def download_thumbnail(url, path):
    """Download thumbnail from URL to specified path"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(path, 'wb') as f:
                        await f.write(await response.read())
                    return path
                return None
    except Exception as e:
        logging.error(f"Error downloading thumbnail: {e}")
        return None

async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name):
    """
    Enhanced document sending function with better error handling
    """
    try:
        reply = await m.reply_text(f"**__Uploading...__** `{name}`")
        start_time = time.time()
        
        # Send the document with progress tracking
        await m.reply_document(
            ka, 
            caption=cc1,
            progress=progress_callback,
            progress_args=(reply,)
        )
        
        count += 1
        await reply.delete()
        
        # Clean up the file
        if os.path.exists(ka):
            os.remove(ka)
            
        return count
    except Exception as e:
        logging.error(f"Error in send_doc: {e}")
        await m.reply_text(f"**__Error uploading file:__** `{str(e)}`")
        return count

async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    """
    Enhanced video sending function with better metadata handling
    """
    try:
        # Generate thumbnail if needed
        thumbnail_path = None
        if thumb == "no":
            subprocess.run(f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{filename}.jpg"', shell=True)
            thumbnail_path = f"{filename}.jpg"
        else:
            # Download the thumbnail if it's a URL
            if thumb.startswith("http"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumb) as response:
                        if response.status == 200:
                            async with aiofiles.open(f"{filename}.thumb.jpg", 'wb') as f:
                                await f.write(await response.read())
                            thumbnail_path = f"{filename}.thumb.jpg"
                        else:
                            # Fallback to generating thumbnail
                            subprocess.run(f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{filename}.jpg"', shell=True)
                            thumbnail_path = f"{filename}.jpg"
            else:
                thumbnail_path = thumb
                
        await prog.delete()
        reply = await m.reply_text(f"**__Uploading...__** `{name}`\n╰────⌈**𝐀𝐍𝐊𝐈𝐓❤️**⌋────╯")

        # Get duration
        dur = int(duration(filename))
        start_time = time.time()

        # Try sending as video, fall back to document if needed
        try:
            await m.reply_video(
                filename,
                caption=cc, 
                supports_streaming=True,
                height=720,
                width=1280,
                thumb=thumbnail_path,
                duration=dur, 
                progress=progress_callback,
                progress_args=(reply,)
            )
        except Exception as e:
            logging.warning(f"Failed to send as video, sending as document: {e}")
            await m.reply_document(
                filename,
                caption=cc, 
                progress=progress_callback,
                progress_args=(reply,)
            )
            
        # Clean up files
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        if os.path.exists(f"{filename}.thumb.jpg"):
            os.remove(f"{filename}.thumb.jpg")
            
        await reply.delete()
    except Exception as e:
        logging.error(f"Error in send_vid: {e}")
        await m.reply_text(f"**__Error uploading video:__** `{str(e)}`")

async def process_audio(event, url, cookies_env_var=None):
    """
    Process and send audio files from various sources
    Compatible with main.py implementation
    """
    cookies = os.getenv(cookies_env_var) if cookies_env_var else None
    temp_cookie_path = None
    if cookies:
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_cookie_file:
            temp_cookie_file.write(cookies)
            temp_cookie_path = temp_cookie_file.name

    random_filename = f"@team_spy_pro_{event.from_user.id}"
    download_path = f"{random_filename}.mp3"
    
    try:
        import tempfile
        from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC
        from mutagen.mp3 import MP3
        import yt_dlp
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{random_filename}.%(ext)s",
            'cookiefile': temp_cookie_path,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': False,
            'noplaylist': True,
        }

        progress_message = await event.reply("**__Starting audio extraction...__**")
        
        # Extract audio using thread pool to prevent blocking
        def sync_extract():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=True)
            except Exception as e:
                logger.error(f"Error extracting audio: {e}")
                return None
                
        loop = asyncio.get_event_loop()
        info_dict = await loop.run_in_executor(None, sync_extract)
        
        if not info_dict:
            await progress_message.edit("**__Failed to extract audio information__**")
            return
            
        title = info_dict.get('title', 'Extracted Audio')

        await progress_message.edit("**__Editing metadata...__**")
        if os.path.exists(download_path):
            try:
                audio_file = MP3(download_path, ID3=ID3)
                if not audio_file.tags:
                    audio_file.add_tags()
                audio_file.tags["TIT2"] = TIT2(encoding=3, text=title)
                audio_file.tags["TPE1"] = TPE1(encoding=3, text="Team SPY")
                audio_file.tags["COMM"] = COMM(encoding=3, lang="eng", desc="Comment", text="Processed by Team SPY")
                thumbnail_url = info_dict.get('thumbnail')
                if thumbnail_url:
                    thumbnail_path = os.path.join(tempfile.gettempdir(), "thumb.jpg")
                    await download_thumbnail(thumbnail_url, thumbnail_path)
                    if os.path.exists(thumbnail_path):
                        with open(thumbnail_path, 'rb') as img:
                            audio_file.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read())
                        os.remove(thumbnail_path)
                audio_file.save()
            except Exception as e:
                logger.error(f"Error editing metadata: {e}")

        if os.path.exists(download_path):
            await progress_message.delete()
            await event.reply_audio(
                download_path, 
                caption=f"**{title}**\n\n**__Powered by Team SPY__**"
            )
        else:
            await event.reply("**__Audio file not found after extraction!__**")
            
    except Exception as e:
        import traceback
        logger.error(f"Error in process_audio: {e}")
        logger.error(traceback.format_exc())
        await event.reply(f"**__An error occurred: {str(e)}__**")
    finally:
        if os.path.exists(download_path):
            os.remove(download_path)
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)
