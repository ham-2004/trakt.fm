from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp

POSTER_WIDTH = 200
POSTER_HEIGHT = 300
GRID_COLS = 3
GRID_ROWS = 2

async def create_titled_image_grid(image_data):
    """
    image_data: List of (poster_url, title) tuples
    Returns: BytesIO object with the WEBP image grid
    """
    grid = Image.new('RGB', (POSTER_WIDTH * GRID_COLS, POSTER_HEIGHT * GRID_ROWS), (0, 0, 0))

    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    async with aiohttp.ClientSession() as session:
        for index, (url, title) in enumerate(image_data):
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        img_data = await resp.read()
                        img = Image.open(BytesIO(img_data)).convert("RGB")
                    else:
                        continue
            except Exception:
                continue

            img = img.resize((POSTER_WIDTH, POSTER_HEIGHT))
            draw = ImageDraw.Draw(img)

            # Draw title bar
            draw.rectangle(
                [(0, POSTER_HEIGHT - 30), (POSTER_WIDTH, POSTER_HEIGHT)],
                fill=(0, 0, 0)
            )
            draw.text(
                (10, POSTER_HEIGHT - 25),
                title,
                font=font,
                fill=(255, 255, 255),
                stroke_width=1,
                stroke_fill=(0, 0, 0)
            )

            x = (index % GRID_COLS) * POSTER_WIDTH
            y = (index // GRID_COLS) * POSTER_HEIGHT
            grid.paste(img, (x, y))

    buffer = BytesIO()
    grid.save(buffer, format="WEBP")
    buffer.seek(0)
    return buffer
