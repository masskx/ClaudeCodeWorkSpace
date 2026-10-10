#!/usr/bin/env python3
"""把 截图源文件/*.html 渲染成 PNG，放进对应文章文件夹的 images/ 里。
每个 html 的 <meta name="shot" content="文章文件夹|文件名.png|宽x高"> 决定输出位置和尺寸。
需要本机有 Chrome / Chromium（会自动找常见路径，也可以用环境变量 CHROME 指定）。输出为 2 倍清晰度，底部空白自动裁掉(需要 Pillow)。\n宽高里的“高”只要不小于内容高度即可。"""
import glob, os, re, shutil, subprocess, sys
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CANDIDATES = [os.environ.get("CHROME", ""), "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
              "google-chrome", "chromium", "chromium-browser",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
chrome = next((c for c in CANDIDATES if c and (os.path.exists(c) or shutil.which(c))), None)
if not chrome:
    sys.exit("找不到 Chrome，请设置环境变量 CHROME")

for src in sorted(glob.glob(os.path.join(HERE, "截图源文件", "*.html"))):
    meta = re.search(r'<meta name="shot" content="([^|]+)\|([^|]+)\|(\d+)x(\d+)"', open(src, encoding="utf-8").read())
    folder, name, w, h = meta.group(1), meta.group(2), meta.group(3), meta.group(4)
    out_dir = os.path.join(ROOT, folder, "imgs")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name)
    subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--window-size=%s,%d" % (w, int(h) + 300),
                    "--screenshot=" + out, "file://" + src], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # 窗口故意开得比内容高，这里把底部多余的空白裁掉，只留一点边距
    img = Image.open(out).convert("RGB")
    bg = img.getpixel((img.width - 1, img.height - 1))
    box = ImageChops.difference(img, Image.new("RGB", img.size, bg)).getbbox()
    if box:
        img.crop((0, 0, img.width, min(img.height, box[3] + 56))).save(out, optimize=True)
    print("生成", folder, name)
