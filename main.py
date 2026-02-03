import requests
import asyncio
import os
import logging
from telegram import Bot
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

logging.basicConfig(level=logging.INFO)

# Configuration
BOT_TOKEN = "8586949573:AAHj1mww960J_3r54nuvXINCBzR0WDV8CGI"
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@THE_DEAL_CHAMBER")
bot = Bot(token=BOT_TOKEN)

# Threshold for updates (500 points)
STEP = 500 

def download_font():
    font_path = "Roboto-Bold.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
        r = requests.get(url)
        with open(font_path, "wb") as f:
            f.write(r.content)
    return font_path

def get_font(size):
    try:
        path = download_font()
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def get_btc_data():
    # Fetching price, 24h change, high, and low
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()[0]
        return {
            "price": float(data["current_price"]),
            "percent": float(data["price_change_percentage_24h"]),
            "high": float(data["high_24h"]),
            "low": float(data["low_24h"])
        }
    except Exception as e:
        logging.error(f"Data fetch error: {e}")
        return None

def create_image(data):
    # Setup Canvas (Orange Background)
    orange_color = "#F7931A"
    img = Image.new("RGB", (1080, 1080), orange_color)
    draw = ImageDraw.Draw(img)
    
    # Fonts
    font_main = get_font(250)    # Big Price
    font_sub = get_font(100)     # Percent
    font_info = get_font(60)     # High/Low
    font_brand = get_font(50)    # Channel Name

    # Text Content
    price_text = f"${int(data['price']):,}"
    percent_text = f"{data['percent']:+.2f}%"
    hl_text = f"24h High: ${int(data['high']):,}  |  24h Low: ${int(data['low']):,}"

    # Draw Elements (All White Text)
    # Price
    draw.text((540, 400), price_text, fill="white", font=font_main, anchor="mm")
    
    # Percentage (with a slight background pill for beauty)
    draw.rounded_rectangle([340, 520, 740, 640], radius=50, fill="#E88300")
    draw.text((540, 580), percent_text, fill="white", font=font_sub, anchor="mm")
    
    # High/Low Info
    draw.text((540, 750), hl_text, fill="white", font=font_info, anchor="mm")
    
    # Branding
    draw.text((540, 980), CHANNEL_USERNAME.upper(), fill="rgba(255,255,255,180)", font=font_brand, anchor="mm")
    
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

async def send_update(data):
    photo_buffer = create_image(data)
    
    # Formatting the caption nicely
    status = "🚀 MOONING" if data['percent'] > 0 else "📉 DIPPING"
    caption = (
        f"<b>BTC {status}</b>\n\n"
        f"💰 <b>Price:</b> ${int(data['price']):,}\n"
        f"📊 <b>24h Change:</b> {data['percent']:+.2f}%\n"
        f"🔼 <b>24h High:</b> ${int(data['high']):,}\n"
        f"🔽 <b>24h Low:</b> ${int(data['low']):,}\n\n"
        f"📢 {CHANNEL_USERNAME}"
    )

    try:
        await bot.send_photo(
            chat_id=CHANNEL_USERNAME, 
            photo=photo_buffer, 
            caption=caption, 
            parse_mode="HTML"
        )
        logging.info(f"✅ Beauty Update Sent: {data['price']}")
    except Exception as e:
        logging.error(f"Telegram Error: {e}")

async def main():
    logging.info("🚀 BTC Beauty Tracker Started...")
    
    last_milestone = None

    while True:
        data = get_btc_data()
        
        if data:
            current_price = data['price']
            current_milestone = (int(current_price) // STEP) * STEP
            
            # Send if it's the first run OR price moved 500 points
            if last_milestone is None or current_milestone != last_milestone:
                logging.info(f"Triggering update for milestone: {current_milestone}")
                await send_update(data)
                last_milestone = current_milestone
            else:
                logging.info(f"Price at {current_price}, no 500pt move yet.")

        # Check every 45 seconds
        await asyncio.sleep(45)

if __name__ == "__main__":
    asyncio.run(main())
    
