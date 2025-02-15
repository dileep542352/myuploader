import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import urllib.parse
import yt_dlp
import cloudscraper
import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

cookies_file_path = os.getenv("COOKIES_FILE_PATH", "youtube_cookies.txt")


# Define aiohttp routes
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://text-leech-bot-for-render.onrender.com/")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

async def start_bot():
    await bot.start()
    print("Bot is up and running")

async def stop_bot():
    await bot.stop()

async def main():
    if WEBHOOK:
        # Start the web server
        app_runner = web.AppRunner(await web_server())
        await app_runner.setup()
        site = web.TCPSite(app_runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server started on port {PORT}")

    # Start the bot
    await start_bot()

    # Keep the program running
    try:
        while True:
            await bot.polling()  # Run forever, or until interrupted
    except (KeyboardInterrupt, SystemExit):
        await stop_bot()
    

async def start_bot():
    await bot.start()
    print("Bot is up and running")

async def stop_bot():
    await bot.stop()

async def main():
    if WEBHOOK:
        # Start the web server
        app_runner = web.AppRunner(await web_server())
        await app_runner.setup()
        site = web.TCPSite(app_runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server started on port {PORT}")

    # Start the bot
    await start_bot()

    # Keep the program running
    try:
        while True:
            await asyncio.sleep(3600)  # Run forever, or until interrupted
    except (KeyboardInterrupt, SystemExit):
        await stop_bot()
        
class Data:
    START = (
        "🌟 Welcome {0}! 🌟\n\n"
    )
# Define the start command handler
@bot.on_message(filters.command("start"))
async def start(client: Client, msg: Message):
    user = await client.get_me()
    mention = user.mention
    start_message = await client.send_message(
        msg.chat.id,
        Data.START.format(msg.from_user.mention)
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Initializing Uploader bot... 🤖\n\n"
        "Progress: [⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Loading features... ⏳\n\n"
        "Progress: [🟥🟥🟥⬜⬜⬜⬜⬜⬜] 25%\n\n"
    )
    
    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "This may take a moment, sit back and relax! 😊\n\n"
        "Progress: [🟧🟧🟧🟧🟧⬜⬜⬜⬜] 50%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Checking Bot Status... 🔍\n\n"
        "Progress: [🟨🟨🟨🟨🟨🟨🟨⬜⬜] 75%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        Data.START.format(msg.from_user.mention) +
        "Checking status Ok... Command Nhi Bataunga **Bot Made BY 𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™👨🏻‍💻**🔍\n\n"
        "Progress:[🟩🟩🟩🟩🟩🟩🟩🟩🟩] 100%\n\n"
    )

@bot.on_message(filters.command(["stop"]) )
async def restart_handler(_, m):
    await m.reply_text("**STOPPED**🛑", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.on_message(filters.command(["ankit","upload"]) )
async def txt_handler(bot: Client, m: Message):
    editable = await m.reply_text(f"** 📁 Send me the TXT file and wait.**")
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    credit = f"𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™🇮🇳"
    try:    
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = []
        for i in content:
            links.append(i.split("://", 1))
        os.remove(x)
    except:
        await m.reply_text("Invalid file input.")
        os.remove(x)
        return
   
    await editable.edit(f"Total links found are **{len(links)}**\n\nSend From where you want to download initial is **1**")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except:
        arg = 1
    await editable.edit("**Enter Your Batch Name or send d for grabing from text filename.**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    if raw_text0 == 'd':
        b_name = file_name
    else:
        b_name = raw_text0

    await editable.edit("**Enter resolution.\n Eg : 480 or 720**")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "144x256"
        elif raw_text2 == "240":
            res = "240x426"
        elif raw_text2 == "360":
            res = "360x640"
        elif raw_text2 == "480":
            res = "480x854"
        elif raw_text2 == "720":
            res = "720x1280"
        elif raw_text2 == "1080":
            res = "1080x1920" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
    
    await editable.edit("**Enter Your Name or send 'de' for use default.\n Eg : 𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™👨🏻‍💻**")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    if raw_text3 == 'de':
        CR = credit
    else:
        CR = raw_text3

    
    await editable.edit("**Enter Your PW Token For MPD URL or send 'unknown' for use default**")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == 'pw':
        token = pw_token
    else:
        token = raw_text4
        
    await editable.edit("Now send the **Thumb url**\n**Eg :** ``\n\nor Send `no`")
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb == "no"

    count =int(raw_text)    
    try:
        for i in range(arg-1, len(links)):

            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
                

            
            elif 'videos.classplusapp' in url:
             headers = {
                    'host': 'api.classplusapp.com',
                    'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9',    
                    'accept-language': 'EN',
                    'api-version': '18',
                    'app-version': '1.4.73.2',
                    'build-number': '35',
                    'connection': 'Keep-Alive',
                    'content-type': 'application/json',
                    'device-details': 'Xiaomi_Redmi 7_SDK-32',
                    'device-id': 'c28d3cb16bbdac01',
                    'region': 'IN',
                    'user-agent': 'Mobile-Android',
                    'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                    'accept-encoding': 'gzip'
             }
             params = (('url', f'{url}'),)
             response = requests.get("https://api.classplusapp.com/cams/uploader/video/jw-signed-url", headers=headers, params=params)
             url = response.json()['url']
             


              


            elif "apps-s3-jw-prod.utkarshapp.com" in url:
                  headers = {  
                          "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",  
                          "Accept-Language": "en-US,en;q=0.9",  
                  }
                  response = requests.get(url, headers=headers)  
                  print(response.text)
            
            
            
            elif '/master.mpd' in url:
             vid_id =  url.split("hls")[-1]
             url =  f"https://pw-links-api.onrender.com/process?v=https://sec1.pw.live/{vid_id}/master.mpd&quality={raw_text2}"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]}'
            
            if '?list' in url:
               video_id = url.split("/embed/")[1].split("?")[0]
               print(video_id)
               url = f"https://www.youtube.com/embed/{video_id}"

            if '/do' in url:               
               url.split("/")[-1].split(".pdf")[0]
               print(pdf_id)
               url = f"https://kgs-v4.akamaized.net/kgs/do/pdfs/{pdf_id}.pdf"
               
               
            if 'khansirvod4.pc.cdn.bitgravity.com' in url:               
               parts = url.split('/')               
               part1 = parts[1]
               part2 = parts[2]
               part3 = parts[3] 
               part4 = parts[4]
               part5 = parts[5]
               
               print(f"PART1: {part1}")
               print(f"PART2: {part2}")
               print(f"PART3: {part3}")
               print(f"PART4: {part4}")
               print(f"PART5: {part5}")
               url = f"https://kgs-v4.akamaized.net/{part2}/{part3}/{part4}/{part5}"
               print(f"URL: {url}")
                
            if '/onlineagriculture' in url:
                # Splitting the URL
               parts = url.split("/")
               # Extracting required components
               vid_id = parts[-4]  # "788682-1714995256"
               hls = parts[-3]  # "hls-78632a"
               quality = parts[-2]  # "360p"
               master = parts[-1]  # "master-9443895.928218126.m3u8"

              # Printing the results
               print(f"Vid ID: {vid_id}")
               print(f"HLS: {hls}")
               print(f"Quality: {quality}")
               print(f"Master: {master}")
               url = f"https://appx-transcoded-videos.akamai.net.in/videos/onlineagriculture-data/{vid_id}/{hls}/{raw_text2}p/{master}"
                
            if 'workers.dev' in url:
             vid_id = url.split("cloudfront.net/")[1].split("/")[0]
             print(vid_id)
             url = f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={raw_text4}"

            if 'livelearn.in' in url:
               parts = url.split("/")
               # Extracting required components
               vid_id = parts[-4]  # "788682-1714995256"
               hls = parts[-3]  # "hls-78632a"
               quality = parts[-2]  # "360p"
               master = parts[-1]  # "master-9443895.928218126.m3u8"

              # Printing the results
               print(f"Vid ID: {vid_id}")
               print(f"HLS: {hls}")
               print(f"Quality: {quality}")
               print(f"Master: {master}")
               url = f"https://appx-transcoded-videos.livelearn.in/videos/englishjaisir-data/{vid_id}/hls/{raw_text2}p/{master}.m3u8"
                
            if '/videos/englishjaisir' in url:
               parts = url.split("/")
               # Extracting required components
               vid_id = parts[-4]  # "788682-1714995256"
               hls = parts[-3]  # "hls-78632a"
               quality = parts[-2]  # "360p"
               master = parts[-1]  # "master-9443895.928218126.m3u8"

              # Printing the results
               print(f"Vid ID: {vid_id}")
               print(f"HLS: {hls}")
               print(f"Quality: {quality}")
               print(f"Master: {master}")
               url = f"https://appx-transcoded-videos.livelearn.in/videos/englishjaisir-data/{vid_id}/{hls}/{raw_text2}p/{master}"
            
            if 'psitoffers.store' in url:
             vid_id = url.split("vid=")[1].split("&")[0]
             print(f"vid_id = {vid_id}")
             url =  f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={raw_text4}"

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
            
            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'

            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:  
                
                cc = f'**<pre><code>🎞️ VID_ID: {str(count).zfill(3)}.</code></pre>\n\n<blockquote>📄 Title: {name1} {res} @Ankit_Shakya73.mkv<blockquote>\n\n<pre><code>🔖 Batch Name:</code></pre> {b_name}</code></pre>\n\n<pre><code>📥 Extracted By :</code></pre> {CR}**\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                cc1 = f'**<pre><code>📁 PDF_ID: {str(count).zfill(3)}.</code></pre>\n\n<blockquote>📄 Title: {name1} @Ankit_Shakya73.pdf<blockquote>\n\n<pre><code>🔖 Batch Name:</code></pre><blockquote>{b_name}<blockquote>\n\n<pre><code>📥 Extracted By :</code></pre>{CR}**\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                    
                
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                
                elif ".pdf" in url:
                    try:
                        await asyncio.sleep(4)
        # Replace spaces with %20 in the URL
                        url = url.replace(" ", "%20")
 
        # Create a cloudscraper session
                        scraper = cloudscraper.create_scraper()

        # Send a GET request to download the PDF
                        response = scraper.get(url)

        # Check if the response status is OK
                        if response.status_code == 200:
            # Write the PDF content to a file
                            with open(f'{name}.pdf', 'wb') as file:
                                file.write(response.content)

            # Send the PDF document
                            await asyncio.sleep(4)
                            copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                            count += 1

            # Remove the PDF file after sending
                            os.remove(f'{name}.pdf')
                        else:
                            await m.reply_text(f"Failed to download PDF: {response.status_code} {response.reason}")

                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue

                
                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue

           
                else:
                    Show = f"❊⟱ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 ⟱❊ »\n\n📄 Title:- `{name}\n\n𝐓𝐚𝐭𝐚𝐥 𝐔𝐑𝐋 🔗 {len(links)}\n\n⌨ 𝐐𝐮𝐥𝐢𝐭𝐲 » {raw_text2}`\n\n**🔗 𝐔𝐑𝐋 »** `{url}`\n\n**𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ ᴀɴᴋɪᴛ sʜᴀᴋʏᴀ"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await m.reply_text(
                    f"⌘ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐮𝐩𝐭𝐞𝐝\n\n⌘ 𝐍𝐚𝐦𝐞 » {name}\n⌘ 𝐋𝐢𝐧𝐤 » `{url}`"
                )
                continue

    except Exception as e:
        await m.reply_text(e)
    await m.reply_text("🔰Done🔰")

@bot.on_message(filters.command(["visionpdf"]) )
async def vision_pdf(bot: Client, m: Message):
    editable = await m.reply_text("**Hello Dear,** I am Text File Downloader📥 Bot.\nI can download **PDFs of vision** from text file one by one.\n\n**Developer: @batmanhcbot👨🏻‍💻** \n**Language:** Python\n**Framework:** 🔥Pyrogram\n\nNow Send Your **TXT File:-**\n")
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)

    path = f"./downloads/{m.chat.id}"

    try:
            with open(x, "r") as f:
                content = f.read()
            content = content.split("\n")

            links = []
            for i in content:
                links.append(i.split(":", 1))
            os.remove(x)
    except:
            await m.reply_text("Invalid file input.☹️")
            os.remove(x)
            return
            
    editable = await m.reply_text(f"Total links found are {len(links)}\n\nSend From where you want to download,\n\nInitial is 1")
    input1: Message = await bot.listen(editable.chat.id)
    count = input1.text
    await input1.delete(True)
    count = int(count)      	
    	            
    await m.reply_text("**Enter Your Batch Name**")
    inputy: Message = await bot.listen(editable.chat.id)
    await inputy.delete(True)
    raw_texty = inputy.text

    await m.reply_text("**Enter Cookies**")
    input2: Message = await bot.listen(editable.chat.id)
    cookie = input2.text
    await input2.delete(True)
    cookies = cookies = {'PHPSESSID': f'{cookie}'}
        
    try:
        for i in range(count, len(links)):

            url = links[i][1]
            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/","").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").strip()[:57]
            name = f'{str(count).zfill(3)}) {name1}'
            cc = f'{str(count).zfill(3)}. {name1}.pdf\n\n**Batch :** {raw_texty}\n\n'
            ka = await helper.vision(url, name, cookies)
            await m.reply_document(ka, caption=cc)
            count += 1
            os.remove(ka)
            time.sleep(3)
    except Exception as e:
        await m.reply_text(e)
    await m.reply_text("**Done✅**")

bot.run()
if __name__ == "__main__":
    asyncio.run(main())
