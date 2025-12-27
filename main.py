import requests
import asyncio
import os
from telegram import Bot
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@THE_DEAL_CHAMBER"
bot = Bot(token=BOT_TOKEN)

LAST_PRICE = None
LAST_MILESTONE = None


def get_btc_price():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    )
    response = requests.get(url, timeout=10)
    data = response.json()

    if "bitcoin" not in data:
        raise Exception("Invalid response from CoinGecko API")

    bitcoin_data = data["bitcoin"]
    price = float(bitcoin_data.get("usd", 0))
    change_percent = float(bitcoin_data.get("usd_24h_change", 0))

    if price == 0:
        raise Exception("Invalid price data from API")

    return price, change_percent


# ✅ SAFE FONT LOADER (NO CRASH EVER)
def get_font(size):
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            size
        )
    except Exception:
        return ImageFont.load_default()


def create_image(price, percent):
    img = Image.new("RGB", (1080, 1080), "#F7931A")
    draw = ImageDraw.Draw(img)

    font_big = get_font(140)
    font_small = get_font(70)
    font_brand = get_font(40)

    price_text = f"${int(price):,}"
    percent_text = f"{percent:+.2f}%"
    brand = "@The_deal_chamber"

    draw.text((540, 360), price_text, fill="black", font=font_big, anchor="mm")
    draw.text(
        (540, 540),
        percent_text,
        fill="green" if percent >= 0 else "red",
        font=font_small,
        anchor="mm"
    )
    draw.text((540, 930), brand, fill="black", font=font_brand, anchor="mm")

    img.save("btc.png")


async def send_update(price, percent):
    create_image(price, percent)

    indicator = "🟢" if percent >= 0 else "🔴"
    caption = (
        f"{indicator} *BTC ${int(price):,}* @The_deal_chamber\n"
        f"{'📈' if percent >= 0 else '📉'} {percent:+.2f}% in 24h"
    )

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
                LAST_MILESTONE = int(price / 500) * 500
                print(
                    f"✅ Initial price: ${price:,.2f} | "
                    f"Milestone: ${LAST_MILESTONE:,}"
                )

            current_milestone = int(price / 500) * 500

            if current_milestone != LAST_MILESTONE:
                direction = "UP" if current_milestone > LAST_MILESTONE else "DOWN"
                print(
                    f"🎯 New milestone {direction}! "
                    f"${LAST_MILESTONE:,} → ${current_milestone:,}"
                )
                await send_update(price, percent)
                LAST_MILESTONE = current_milestone
            else:
                print(
                    f"Current: ${price:,.2f} | "
                    f"24h: {percent:+.2f}% | "
                    f"Milestone: ${LAST_MILESTONE:,}"
                )

            await asyncio.sleep(60)

        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
