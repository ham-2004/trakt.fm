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


async def create_titled_image_grids(image_data, max_width=1200, max_height=800, min_cols=2, max_cols=4):
    """
    Creates an image grid that automatically adjusts layout based on number of items.

    Args:
        image_data: List of (poster_url, title) tuples
        max_width: Maximum width of the output image
        max_height: Maximum height of the output image
        min_cols: Minimum number of columns to use
        max_cols: Maximum number of columns to use

    Returns:
        BytesIO object with the WEBP image grid
    """
    if not image_data:
        return None

    # Calculate optimal grid layout
    num_items = len(image_data)
    num_cols = min(max_cols, max(min_cols, int(num_items ** 0.5) + 1))
    num_rows = (num_items + num_cols - 1) // num_cols

    # Calculate poster dimensions based on grid size and max dimensions
    poster_width = min(300, max_width // num_cols)
    poster_height = int(poster_width * 1.5)  # Standard poster aspect ratio

    # Adjust if total height would exceed max_height
    while num_rows * poster_height > max_height and poster_height > 100:
        poster_height -= 10
        poster_width = int(poster_height / 1.5)

    # Create the grid image
    grid = Image.new('RGB',
                     (poster_width * num_cols, poster_height * num_rows),
                     (0, 0, 0))

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
                    # else:
                    #     # Use fallback image if download fails
                    #     async with session.get(FALLBACK_POSTER) as resp:
                    #         img_data = await resp.read()
                    #         img = Image.open(BytesIO(img_data)).convert("RGB")
            except Exception as e:
                print(f"Error loading image {url}: {e}")
                continue

            # Resize and add title
            img = img.resize((poster_width, poster_height))
            draw = ImageDraw.Draw(img)

            # Draw title bar (only if there's space)
            if poster_height > 100:  # Only add titles if posters are large enough
                title_bar_height = min(30, poster_height // 5)
                draw.rectangle(
                    [(0, poster_height - title_bar_height),
                     (poster_width, poster_height)],
                    fill=(0, 0, 0)
                )

                # Truncate title if too long
                max_chars = poster_width // 10  # Approximate based on font size
                display_title = (title[:max_chars - 3] + '...') if len(title) > max_chars else title

                draw.text(
                    (10, poster_height - title_bar_height + 5),
                    display_title,
                    font=font,
                    fill=(255, 255, 255),
                    stroke_width=1,
                    stroke_fill=(0, 0, 0)
                )

            # Calculate position in grid
            x = (index % num_cols) * poster_width
            y = (index // num_cols) * poster_height
            grid.paste(img, (x, y))

    # Convert to BytesIO
    img_bytes = BytesIO()
    grid.save(img_bytes, format='WEBP', quality=85)
    img_bytes.seek(0)

    return img_bytes
