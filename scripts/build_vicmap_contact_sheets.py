import csv, math, os, urllib.request
from PIL import Image, ImageDraw, ImageFont

CSV_PATH = r'D:\xwechat_files\wxid_fynu0rcjs47f21_b973\msg\file\2026-08\vicmap_qa_sample(1).csv'
OUT_DIR = r'E:\Github\active-together\tmp\vicmap_satellite'
ZOOM = 18
THUMB = 300
COLS, ROWS = 3, 4

os.makedirs(OUT_DIR, exist_ok=True)
font = ImageFont.load_default(size=16)

def world_xy(lat, lon, zoom):
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return x, y

def centered_image(lat, lon):
    x, y = world_xy(lat, lon, ZOOM)
    tx, ty = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - tx, y - ty
    canvas = Image.new('RGB', (768, 768), 'white')
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            url = f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{ZOOM}/{ty+oy}/{tx+ox}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Codex-Vicmap-QA/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                tile_path = os.path.join(OUT_DIR, '_tile.jpg')
                data = response.read()
            from io import BytesIO
            tile = Image.open(BytesIO(data)).convert('RGB')
            canvas.paste(tile, ((ox + 1) * 256, (oy + 1) * 256))
    cx, cy = 256 + fx * 256, 256 + fy * 256
    half = THUMB // 2
    crop = canvas.crop((int(cx-half), int(cy-half), int(cx+half), int(cy+half)))
    draw = ImageDraw.Draw(crop)
    draw.line((half-10, half, half+10, half), fill='red', width=3)
    draw.line((half, half-10, half, half+10), fill='red', width=3)
    return crop

with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

for page_start in range(0, len(rows), COLS * ROWS):
    page_rows = rows[page_start:page_start + COLS * ROWS]
    sheet = Image.new('RGB', (COLS * THUMB, ROWS * (THUMB + 56)), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(page_rows):
        image = centered_image(float(row['latitude']), float(row['longitude']))
        col, rr = i % COLS, i // COLS
        x0, y0 = col * THUMB, rr * (THUMB + 56)
        sheet.paste(image, (x0, y0 + 56))
        title = f"#{row['sample_id']} {row['feature_subtype']}"
        name = row['display_name'][:37]
        draw.text((x0 + 4, y0 + 4), title, fill='black', font=font)
        draw.text((x0 + 4, y0 + 26), name, fill='black', font=font)
    page = page_start // (COLS * ROWS) + 1
    sheet.save(os.path.join(OUT_DIR, f'contact_{page:02d}.jpg'), quality=90)

print(f'Created {math.ceil(len(rows)/(COLS*ROWS))} contact sheets in {OUT_DIR}')
