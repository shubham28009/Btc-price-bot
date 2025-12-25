import requests
import asyncio
from telegram import Bot
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = "8586949573:AAHj1mww960J_3r54nuvXINCBzR0WDV8CGI"
CHANNEL_USERNAME = "@the_deal_chamber"

bot = Bot(token=BOT_TOKEN)

LAST_PRICE = None
LAST_MILESTONE = None  # Track last milestone reached (88500, 89000, etc.)

def get_btc_price():
    # Using CoinGecko API (no IP restrictions, free tier available)
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    response = requests.get(url)
    data = response.json()
    
    if "bitcoin" not in data:
        raise Exception("Invalid response from CoinGecko API")
    
    bitcoin_data = data["bitcoin"]
    price = float(bitcoin_data.get("usd", 0))
    change_percent = float(bitcoin_data.get("usd_24h_change", 0))
    
    if price == 0:
        raise Exception("Invalid price data from API")
    
    return price, change_percent

def create_image(price, percent):
    img = Image.new("RGB", (1080, 1080), "#F7931A")
    draw = ImageDraw.Draw(img)

    # Load fonts
    font_big = None
    font_small = None
    font_brand = None
    
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    
    for path in font_paths:
        try:
            font_big = ImageFont.truetype(path, 200)
            font_small = ImageFont.truetype(path, 130)
            font_brand = ImageFont.truetype(path, 70)
            break
        except:
            continue
    
    if font_big is None:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_brand = ImageFont.load_default()

    price_text = f"${int(price):,}"
    percent_text = f"{percent:+.2f}%"
    brand = "@the_deal_chamber"

    # Draw small price text at upper part
    draw.text((540, 280), price_text, font=font_big, fill="black", anchor="mm")
    
    # Draw larger percentage text
    draw.text((540, 550), percent_text, font=font_small, fill="black", anchor="mm")
    
    # Draw channel name in beige/cream color at bottom
    draw.text((540, 900), brand, font=font_brand, fill="#E8D4A8", anchor="mm")

    img.save("btc.png")

async def send_update(price, percent):
    create_image(price, percent)
    indicator = '🟢' if percent >= 0 else '🔴'
    caption = f"{indicator} *BTC ${int(price):,}* *@the_deal_chamber*\n*💹 {percent:+.2f}%* in 24h"
    with open("btc.png", "rb") as photo:
        await bot.send_photo(
            chat_id=CHANNEL_USERNAME,
            photo=photo,
            caption=caption,
            parse_mode="Markdown"
        )
    print(f"✅ Sent update: BTC ${price:,.2f} ({percent:+.2f}%)")

async def main():
    global LAST_PRICE, LAST_MILESTONE
    print("🤖 Bitcoin monitor started...")
    
    while True:
        try:
            price, percent = get_btc_price()

            if LAST_PRICE is None:
                LAST_PRICE = price
                # Calculate initial milestone (round down to nearest 500)
                LAST_MILESTONE = int(price / 500) * 500
                print(f"✅ Initial price: ${price:,.2f} | Milestone: ${LAST_MILESTONE:,}")

            # Calculate current milestone (every $500: 88500, 89000, etc.)
            current_milestone = int(price / 500) * 500
            
            # Send update if we've reached a new milestone
            if current_milestone > LAST_MILESTONE:  # Price moved UP to new milestone
                print(f"🎯 New milestone UP! ${LAST_MILESTONE:,.2f} → ${current_milestone:,.2f}")
                await send_update(price, percent)
                LAST_MILESTONE = current_milestone
            elif current_milestone < LAST_MILESTONE:  # Price moved DOWN to new milestone
                print(f"🎯 New milestone DOWN! ${LAST_MILESTONE:,.2f} → ${current_milestone:,.2f}")
                await send_update(price, percent)
                LAST_MILESTONE = current_milestone
            else:
                next_up = LAST_MILESTONE + 500
                next_down = LAST_MILESTONE - 500
                if price >= LAST_MILESTONE:
                    distance = next_up - price
                    print(f"Current: ${price:,.2f} | 24h: {percent:+.2f}% | Next UP: ${next_up:,.2f} (${distance:+,.2f})")
                else:
                    distance = price - next_down
                    print(f"Current: ${price:,.2f} | 24h: {percent:+.2f}% | Next DOWN: ${next_down:,.2f} (${distance:+,.2f})")

            await asyncio.sleep(60)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
