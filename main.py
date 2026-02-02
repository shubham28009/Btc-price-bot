import requests
import asyncio
import os
import logging
from telegram import Bot
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

logging.basicConfig(level=logging.INFO)

# Configuration
# ✅ BOT TOKEN UPDATED
BOT_TOKEN = "8586949573:AAHj1mww960J_3r54nuvXINCBzR0WDV8CGI"
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@THE_DEAL_CHAMBER")
bot = Bot(token=BOT_TOKEN)

# Threshold for updates
STEP = 500 

def download_font():
    font_path = "Roboto-Bold.ttf"
    if not os.path.exists(font_path):
        logging.info("📥 Font downloading...")
        url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
        r = requests.get(url)
        with open(font_path, "wb") as f:
            f.write(r.content)
        logging.info("✅ Font downloaded!")
    return font_path

def get_font(size):
    try:
        path = download_font()
        return ImageFont.truetype(path, size)
    except Exception as e:
        logging.warning(f"Font error: {e}. Defaulting.")
        return ImageFont.load_default()

def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        bitcoin_data = data["bitcoin"]
        return float(bitcoin_data["usd"]), float(bitcoin_data["usd_24h_change"])
    except Exception as e:
        logging.error(f"Price fetch error: {e}")
        return None, None

def create_image(price, percent):
    # Dynamic background: Green for up, Red for down
    bg_color = "#008000" if percent >= 0 else "#8B0000"
    img = Image.new("RGB", (1080, 1080), bg_color)
    draw = ImageDraw.Draw(img)
    
    font_big = get_font(240)    
    font_small = get_font(130)  
    font_brand = get_font(60)   

    price_text = f"${int(price):,}"
    percent_text = f"{percent:+.2f}%"

    draw.text((540, 420), price_text, fill="white", font=font_big, anchor="mm")
    draw.text((540, 620), percent_text, fill="white", font=font_small, anchor="mm")
    draw.text((540, 950), CHANNEL_USERNAME, fill="rgba(255,255,255,128)", font=font_brand, anchor="mm")
    
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

async def send_update(price, percent):
    photo_buffer = create_image(price, percent)
    indicator = "🟢" if percent >= 0 else "🔴"
    
    caption = (
        f"{indicator} <b>BTC ALERT: ${int(price):,}</b>\n"
        f"{'📈' if percent >= 0 else '📉'} {percent:+.2f}% in 24h\n"
        f"📢 {CHANNEL_USERNAME}"
    )

    try:
        await bot.send_photo(
            chat_id=CHANNEL_USERNAME, 
            photo=photo_buffer, 
            caption=caption, 
            parse_mode="HTML"
        )
        logging.info(f"✅ Alert Sent at ${price}")
    except Exception as e:
        logging.error(f"Telegram Send Error: {e}")

async def main():
    logging.info("🚀 BTC Tracker Bot Started...")
    
    # Initialize with current milestone
    price, _ = get_btc_price()
    if price:
        last_milestone = (int(price) // STEP) * STEP
        logging.info(f"Initial milestone set at: {last_milestone}")
    else:
        last_milestone = 0

    while True:
        current_price, percent = get_btc_price()
        
        if current_price:
            # Calculate current milestone (e.g., 75200 becomes 75000)
            current_milestone = (int(current_price) // STEP) * STEP
            
            # If the milestone has changed (moved up or down by 500)
            if current_milestone != last_milestone:
                logging.info(f"Price crossed milestone: {current_milestone}")
                await send_update(current_price, percent)
                last_milestone = current_milestone
            else:
                logging.info(f"Price: {current_price} (Waiting for next {STEP} point move)")

        # Check every 30 seconds to catch fast moves
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
    
