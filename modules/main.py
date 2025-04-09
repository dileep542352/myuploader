import os
import re
import sys
import time
import asyncio
import random
import string
import requests
import tempfile
import subprocess
import urllib.parse
import logging
import yt_dlp
import cloudscraper
import aiohttp
import aiofiles
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC
from mutagen.mp3 import MP3
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from aiohttp import web
from pyromod import listen

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration (Replace with your actual credentials)
API_ID = "23298276"  # Replace with your Telegram API ID
API_HASH = "0fa5ea46f81eb24548cfc66b5d0f6107"  # Replace with your Telegram API Hash
BOT_TOKEN = "8098279575:AAGAMKgRgSW4b0TvbE6njoYtpntTCiONw3E"  # Replace with your Bot Token
WEBHOOK = False  # Set to True if using a web server
PORT = 8000  # Port for web server if WEBHOOK is True

# Initialize client
bot = Client(
    "bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN
)
thread_pool = ThreadPoolExecutor()
ongoing_downloads = {}

# Custom exception handler for asyncio
def handle_exception(loop, context):
    msg = context.get("exception", context["message"])
    logger.error(f"Caught exception: {msg}")
    logger.error(f"Context: {context}")

# Web server setup
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("Bot is running")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

async def start_bot():
    try:
        await bot.start()
        me = await bot.get_me()
        logger.info(f"Bot started successfully! Username: @{me.username}")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

async def stop_bot():
    await bot.stop()
    logger.info("Bot stopped")

async def main():
    # Set up asyncio exception handler
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)
    
    try:
        if WEBHOOK:
            app_runner = web.AppRunner(await web_server())
            await app_runner.setup()
            site = web.TCPSite(app_runner, "0.0.0.0", PORT)
            await site.start()
            logger.info(f"Web server started on port {PORT}")
        
        await start_bot()
        logger.info("Main loop starting...")
        
        # Keep the bot running
        while True:
            await asyncio.sleep(3600)
            logger.info("Bot still running...")
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received shutdown signal")
        await stop_bot()
    except Exception as e:
        logger.error(f"Critical error in main loop: {e}")
        await stop_bot()

# Utility Functions
def get_random_string(length=7):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

async def download_thumbnail_async(url, path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(path, 'wb') as f:
                        await f.write(await response.read())
                    return path
        return None
    except Exception as e:
        logger.error(f"Error downloading thumbnail: {e}")
        return None

async def extract_audio_async(ydl_opts, url):
    def sync_extract():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None
    return await asyncio.get_event_loop().run_in_executor(thread_pool, sync_extract)

async def process_audio(event, url, cookies_env_var=None):
    cookies = os.getenv(cookies_env_var) if cookies_env_var else None
    temp_cookie_path = None
    if cookies:
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_cookie_file:
            temp_cookie_file.write(cookies)
            temp_cookie_path = temp_cookie_file.name

    random_filename = f"@team_spy_pro_{event.from_user.id}"
    download_path = f"{random_filename}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{random_filename}.%(ext)s",
        'cookiefile': temp_cookie_path,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': False,
        'noplaylist': True,
    }

    progress_message = await event.reply("**__Starting audio extraction...__**")
    try:
        info_dict = await extract_audio_async(ydl_opts, url)
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
                    await download_thumbnail_async(thumbnail_url, thumbnail_path)
                    if os.path.exists(thumbnail_path):
                        with open(thumbnail_path, 'rb') as img:
                            audio_file.tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read())
                        os.remove(thumbnail_path)
                audio_file.save()
            except Exception as e:
                logger.error(f"Error editing metadata: {e}")

        if os.path.exists(download_path):
            await progress_message.delete()
            await bot.send_audio(
                event.chat.id, 
                download_path, 
                caption=f"**{title}**\n\n**__Powered by Team SPY__**"
            )
        else:
            await event.reply("**__Audio file not found after extraction!__**")
    except Exception as e:
        logger.error(f"Error in process_audio: {e}")
        await event.reply(f"**__An error occurred: {str(e)}__**")
    finally:
        if os.path.exists(download_path):
            os.remove(download_path)
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)

def humanbytes(size):
    if not size:
        return "0 B"
    power = 2**10
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    n = 0
    while size > power and n < len(units) - 1:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"

async def progress_callback(current, total, message):
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
            f"Done: {humanbytes(current)} / {humanbytes(total)}\n"
            f"Speed: {humanbytes(speed)}/s\n"
            f"ETA: {int(eta)}s"
        )
        await message.edit(text)
    except Exception as e:
        logger.error(f"Error in progress callback: {e}")

# Command Handlers
@bot.on_message(filters.command("start"))
async def start(client: Client, msg: Message):
    logger.info(f"Start command received from {msg.from_user.first_name}")
    await msg.reply_text(
        "🌟 Welcome to the Ultimate Downloader Bot! 🌟\n\n"
        "Supports YouTube, Instagram, MPD, PDFs, and more!\n"
        "Use /txtdl for batch downloads from TXT files.\n"
        "Bot Made by 𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™👨🏻‍💻"
    )

@bot.on_message(filters.command("stop"))
async def stop_handler(_, m):
    await m.reply_text("**STOPPED**🛑", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("txtdl"))
async def txt_handler(bot: Client, m: Message):
    user_id = m.from_user.id
    if user_id in ongoing_downloads:
        await m.reply_text("**You already have an ongoing download. Please wait!**")
        return

    logger.info(f"txtdl command received from user {user_id}")
    editable = await m.reply_text("**📁 Send me the TXT file with URLs.**")
    
    try:
        input_msg = await bot.listen(editable.chat.id)
        x = await input_msg.download()
        await input_msg.delete(True)
        
        if not x:
            await editable.edit("Failed to download the file")
            return
            
        file_name, _ = os.path.splitext(os.path.basename(x))
        credit = "𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™🇮🇳"

        try:
            with open(x, "r") as f:
                content = f.read()
            links = [line.strip() for line in content.split("\n") if line.strip()]
            os.remove(x)
        except Exception as e:
            await m.reply_text(f"Invalid file input: {str(e)}")
            os.remove(x)
            return

        if not links:
            await editable.edit("No valid links found in the file")
            return
            
        await editable.edit(f"Total links found: **{len(links)}**\n\nSend starting index (default is 1)")
        input0 = await bot.listen(editable.chat.id)
        try:
            start_index = int(input0.text) if input0.text and input0.text.isdigit() else 1
        except:
            start_index = 1
        await input0.delete(True)

        await editable.edit("**Enter Batch Name or 'd' for default (filename).**")
        input1 = await bot.listen(editable.chat.id)
        b_name = file_name if input1.text == 'd' else input1.text
        await input1.delete(True)

        await editable.edit("**Enter type: 'video', 'audio', or 'pdf'.**")
        input2 = await bot.listen(editable.chat.id)
        dl_type = input2.text.lower()
        await input2.delete(True)

        res = "UN"
        if dl_type == "video":
            await editable.edit("**Enter resolution (e.g., 480, 720, 1080).**")
            input3 = await bot.listen(editable.chat.id)
            raw_res = input3.text
            res = {"144": "144x256", "240": "240x426", "360": "360x640", "480": "480x854", "720": "720x1280", "1080": "1080x1920"}.get(raw_res, "UN")
            await input3.delete(True)

        await editable.edit("**Enter Your Name or 'de' for default.**")
        input4 = await bot.listen(editable.chat.id)
        CR = credit if input4.text == 'de' else input4.text
        await input4.delete(True)

        await editable.edit("**Enter PW Token for MPD URL or 'unknown'.**")
        input5 = await bot.listen(editable.chat.id)
        token = input5.text if input5.text != 'unknown' else "unknown"
        await input5.delete(True)

        await editable.edit("**Send Thumbnail URL or 'no'.**")
        input6 = await bot.listen(editable.chat.id)
        thumb = input6.text if input6.text.startswith("http") else "no"
        await input6.delete(True)
        
        thumb_path = None
        if thumb != "no":
            thumb_path = "thumb.jpg"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumb) as response:
                        if response.status == 200:
                            async with aiofiles.open(thumb_path, 'wb') as f:
                                await f.write(await response.read())
                        else:
                            thumb_path = None
            except Exception as e:
                logger.error(f"Error downloading thumbnail: {e}")
                thumb_path = None

        await editable.delete()
        ongoing_downloads[user_id] = True
        
        success_count = 0
        error_count = 0
        
        try:
            for i in range(start_index - 1, len(links)):
                url = links[i]
                name = f"{str(i + 1).zfill(3)}) {url.split('/')[-1][:60].replace('.pdf', '')}"
                caption = f"{'🎞️ 𝐕𝐈𝐃' if dl_type == 'video' else '🎵 𝐀𝐔𝐃' if dl_type == 'audio' else '📁 𝐏𝐃𝐅'}_𝐈𝐃: {str(i + 1).zfill(3)}.\n\n📝 𝐓𝐈𝐓𝐋𝐄: {name}\n\n📚 𝐁𝐀𝐓𝐂𝐇: {b_name}\n\n✨ 𝐄𝐗𝐓𝐑𝐀𝐂𝐓𝐄𝐃 𝐁𝐘: {CR}"

                if dl_type == "audio":
                    try:
                        await process_audio(m, url, "INSTA_COOKIES" if "instagram.com" in url else "YT_COOKIES" if "youtu" in url else None)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error processing audio for URL {url}: {e}")
                        await m.reply_text(f"Error processing audio for URL {url}: {str(e)}")
                        error_count += 1
                    continue

                if dl_type == "pdf" or ".pdf" in url.lower():
                    try:
                        scraper = cloudscraper.create_scraper()
                        response = scraper.get(url.replace(" ", "%20"))
                        if response.status_code == 200:
                            pdf_path = f"{name}.pdf"
                            with open(pdf_path, 'wb') as file:
                                file.write(response.content)
                            await bot.send_document(
                                m.chat.id, 
                                pdf_path, 
                                caption=caption
                            )
                            os.remove(pdf_path)
                            success_count += 1
                        else:
                            await m.reply_text(f"Failed to download PDF: {response.status_code}")
                            error_count += 1
                    except Exception as e:
                        logger.error(f"Error processing PDF for URL {url}: {e}")
                        await m.reply_text(f"Error processing PDF for URL {url}: {str(e)}")
                        error_count += 1
                    continue

                # Video handling
                cookies_env = None
                if "instagram.com" in url:
                    cookies_env = "INSTA_COOKIES"
                elif "youtube.com" in url or "youtu.be" in url:
                    cookies_env = "YT_COOKIES"
                elif "visionias" in url:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, headers={
                                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36'
                            }) as resp:
                                text = await resp.text()
                                match = re.search(r"(https://.*?playlist.m3u8.*?)\"", text)
                                if match:
                                    url = match.group(1)
                                else:
                                    await m.reply_text(f"Failed to extract m3u8 URL from {url}")
                                    error_count += 1
                                    continue
                    except Exception as e:
                        logger.error(f"Error processing visionias URL: {e}")
                        await m.reply_text(f"Error processing URL {url}: {str(e)}")
                        error_count += 1
                        continue
                elif "classplusapp" in url:
                    try:
                        response = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={
                            'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'
                        })
                        if response.status_code == 200:
                            url = response.json()['url']
                        else:
                            await m.reply_text(f"Failed to get signed URL for {url}: {response.status_code}")
                            error_count += 1
                            continue
                    except Exception as e:
                        logger.error(f"Error processing classplus URL: {e}")
                        await m.reply_text(f"Error processing URL {url}: {str(e)}")
                        error_count += 1
                        continue

                cookies = os.getenv(cookies_env) if cookies_env else None
                temp_cookie_path = None
                if cookies:
                    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_cookie_file:
                        temp_cookie_file.write(cookies)
                        temp_cookie_path = temp_cookie_file.name

                download_path = f"{name}.mp4"
                ytf = f"b[height<={res.split('x')[0]}]/bv[height<={res.split('x')[0]}]+ba/b/bv+ba" if "youtu" not in url else "b[height<=1080][ext=mp4]/bv[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
                ydl_opts = {
                    'outtmpl': download_path,
                    'format': ytf,
                    'cookiefile': temp_cookie_path,
                    'writethumbnail': True,
                }

                # Process special URL types
                if "master.mpd" in url:
                    vid_id = url.split("/")[-2]
                    url = f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={token}"
                elif "workers.dev" in url:
                    parts = url.split("cloudfront.net/")
                    if len(parts) > 1:
                        vid_id = parts[1].split("/")[0]
                        url = f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={token}"
                elif "onlineagriculture" in url:
                    parts = url.split("/")
                    if len(parts) >= 4:
                        vid_id, hls, quality, master = parts[-4], parts[-3], parts[-2], parts[-1]
                        url = f"https://appx-transcoded-videos.akamai.net.in/videos/onlineagriculture-data/{vid_id}/{hls}/{res.split('x')[0]}p/{master}"
                elif "livelearn.in" in url or "englishjaisir" in url:
                    parts = url.split("/")
                    if len(parts) >= 4:
                        vid_id, hls, quality, master = parts[-4], parts[-3], parts[-2], parts[-1]
                        url = f"https://appx-transcoded-videos.livelearn.in/videos/englishjaisir-data/{vid_id}/{hls}/{res.split('x')[0]}p/{master}"
                elif "psitoffers.store" in url:
                    parts = url.split("vid=")
                    if len(parts) > 1:
                        vid_id = parts[1].split("&")[0]
                        url = f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={token}"

                prog = await m.reply_text(f"📥 Downloading: `{name}`\n\n🔗 URL: `{url}`")
                try:
                    def download_with_ydl():
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                    
                    # Run yt-dlp in a thread to avoid blocking
                    await asyncio.get_event_loop().run_in_executor(thread_pool, download_with_ydl)
                    
                    if os.path.exists(download_path):
                        upload_prog = await m.reply_text("**__Starting Upload...__**")
                        upload_prog.start_time = time.time()
                        
                        try:
                            await bot.send_video(
                                m.chat.id, 
                                download_path, 
                                caption=caption, 
                                thumb=thumb_path,
                                progress=progress_callback, 
                                progress_args=(upload_prog,)
                            )
                            success_count += 1
                        except FloodWait as e:
                            logger.warning(f"FloodWait: Sleeping for {e.x} seconds")
                            await asyncio.sleep(e.x)
                            await bot.send_video(
                                m.chat.id, 
                                download_path, 
                                caption=caption, 
                                thumb=thumb_path
                            )
                            success_count += 1
                        except Exception as e:
                            logger.error(f"Error uploading video: {e}")
                            await m.reply_text(f"Error uploading video: {str(e)}")
                            error_count += 1
                            
                        await upload_prog.delete()
                        os.remove(download_path)
                    else:
                        await m.reply_text("**__File not found after download!__**")
                        error_count += 1
                except Exception as e:
                    logger.error(f"Error downloading/uploading {url}: {e}")
                    await m.reply_text(f"Error: {str(e)}")
                    error_count += 1
                finally:
                    await prog.delete()
                    if temp_cookie_path and os.path.exists(temp_cookie_path):
                        os.remove(temp_cookie_path)
                
                # Add a small delay between downloads
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Batch error: {e}")
            await m.reply_text(f"Batch Error: {str(e)}")
        finally:
            ongoing_downloads.pop(user_id, None)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
                
        await m.reply_text(f"🔰 Done 🔰\nSuccessfully processed: {success_count}\nErrors: {error_count}")
        
    except Exception as e:
        logger.error(f"Error in txtdl handler: {e}")
        await m.reply_text(f"An error occurred: {str(e)}")
        ongoing_downloads.pop(user_id, None)

# Main Execution
if __name__ == "__main__":
    logger.info("Bot script starting...")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Critical error in main execution: {e}")
