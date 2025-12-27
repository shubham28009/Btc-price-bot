import requests
import asyncio
import os
import logging
from telegram import Bot
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
# Railway/GitHub environment se tokens lega
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@THE_DEAL_CHAMBER")
bot = Bot(token=BOT_TOKEN)

# ✅ SAFE FONT LOADER (Size fix karne ke liye)
def get_font(size):
    # Railway/Linux server par ye fonts milti hain
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "arial.ttf" # Agar aapne project folder me rakha ho
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    
    # Agar koi font nahi mila to default (size issue yahan hota hai)
    logging.warning("System font nahi mila, default use ho raha hai.")
    return ImageFont.load_default()

def get_btc_price():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    )
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if "bitcoin" not in data:
            raise Exception("Invalid response from CoinGecko API")
        
        bitcoin_data = data["bitcoin"]
        price = float(bitcoin_data.get("usd", 0))
        change_percent = float(bitcoin_data.get("usd_24h_change", 0))
        
        if price == 0:
            raise Exception("Invalid price data from API")
        return price, change_percent
    except Exception as e:
        logging.error(f"Price error: {e}")
        return None, None

def create_image(price, percent):
    # 1080x1080 ke liye bade font sizes
    img = Image.new("RGB", (1080, 1080), "#F7931A")
    draw = ImageDraw.Draw(img)
    
    # Font Sizes badha diye gaye hain
    font_big = get_font(220)    # Price ke liye
    font_small = get_font(120)  # Percentage ke liye
    font_brand = get_font(60)   # Username ke liye

    price_text = f"${int(price):,}"
    percent_text = f"{percent:+.2f}%"
    brand = CHANNEL_USERNAME

    # Drawing (Centers align)
    draw.text((540, 420), price_text, fill="black", font=font_big, anchor="mm")
    draw.text(
        (540, 620), 
        percent_text, 
        fill="#004d00" if percent >= 0 else "#8b0000", 
        font=font_small, 
        anchor="mm"
    )
    draw.text((540, 950), brand, fill="white", font=font_brand, anchor="mm")
    
    # BytesIO use kar rahe hain taaki Railway par file permission error na aaye
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

async def send_update():
    price, percent = get_btc_price()
    if price is None:
        return

    # Image generate karein (memory mein)
    photo_buffer = create_image(price, percent)
    
    indicator = "🟢" if percent >= 0 else "🔴"
    caption = (
        f"{indicator} *BTC ${int(price):,}*\n"
        f"{'📈' if percent >= 0 else '📉'} {percent:+.2f}% in 24h\n"
        f"📢 {CHANNEL_USERNAME}"
    )

    try:
        await bot.send_photo(
            chat_id=CHANNEL_USERNAME,
            photo=photo_buffer,
            caption=caption,
            parse_mode="Markdown"
        )
        logging.info(f"Update sent: {price}")
    except Exception as e:
        logging.error(f"Send error: {e}")

async def main():
    logging.info("Bot is starting...")
    while True:
        await send_update()
        # 1 ghante ka wait (3600 seconds)
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
