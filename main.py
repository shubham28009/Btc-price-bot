import requests
import asyncio
import os
import logging
from telegram import Bot
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@THE_DEAL_CHAMBER")
bot = Bot(token=BOT_TOKEN)

# ✅ FONT DOWNLOADER: Isse font hamesha bada aayega
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
        logging.warning(f"Font error: {e}. Default use ho raha hai.")
        return ImageFont.load_default()

def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        bitcoin_data = data["bitcoin"]
        return float(bitcoin_data["usd"]), float(bitcoin_data["usd_24h_change"])
    except Exception as e:
        logging.error(f"Price error: {e}")
        return None, None

def create_image(price, percent):
    img = Image.new("RGB", (1080, 1080), "#F7931A")
    draw = ImageDraw.Draw(img)
    
    # Sizes badha diye gaye hain
    font_big = get_font(240)    # Price (Aur bada kiya)
    font_small = get_font(130)  # Percentage
    font_brand = get_font(60)   # Username

    price_text = f"${int(price):,}"
    percent_text = f"{percent:+.2f}%"

    draw.text((540, 420), price_text, fill="black", font=font_big, anchor="mm")
    draw.text((540, 620), percent_text, fill="#004d00" if percent >= 0 else "#8b0000", font=font_small, anchor="mm")
    draw.text((540, 950), CHANNEL_USERNAME, fill="white", font=font_brand, anchor="mm")
    
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

async def send_update():
    price, percent = get_btc_price()
    if price is None: return

    photo_buffer = create_image(price, percent)
    indicator = "🟢" if percent >= 0 else "🔴"
    caption = f"{indicator} *BTC ${int(price):,}*\n{'📈' if percent >= 0 else '📉'} {percent:+.2f}% in 24h\n📢 {@THE_DEAL_CHAMBER}"

    try:
        await bot.send_photo(chat_id=CHANNEL_USERNAME, photo=photo_buffer, caption=caption, parse_mode="Markdown")
        logging.info(f"Update sent: {price}")
    except Exception as e:
        logging.error(f"Send error: {e}")

async def main():
    logging.info("Bot is starting...")
    while True:
        await send_update()
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
