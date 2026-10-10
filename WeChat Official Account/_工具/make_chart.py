#!/usr/bin/env python3
"""生成第 03 篇用的示意折线图的截图源文件(数据是演示用的，不是真实实验结果)。"""
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, L, R, T, B = 560, 400, 64, 24, 24, 56
xs = list(range(0, 51, 2))

def curve(plateau, tau, wob):
    return [plateau - (plateau - 40) * math.exp(-x / tau) + wob * math.sin(x * 1.7) * math.exp(-x / 40) for x in xs]

series = [("Baseline", curve(76.0, 11, 0.5), "#8a8f9c", "6 4"),
          ("+ Module A", curve(77.2, 10, 0.5), "#e08a2c", ""),
          ("Ours", curve(78.6, 9, 0.5), "#2f6fed", "")]
ymin, ymax = 40, 80
px = lambda x: L + (W - L - R) * x / 50
py = lambda y: T + (H - T - B) * (ymax - y) / (ymax - ymin)
out = []
for yv in range(40, 81, 10):
    out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e5e7ec"/>' % (L, py(yv), W - R, py(yv)))
    out.append('<text x="%d" y="%.1f" text-anchor="end" font-size="13" fill="#444">%d</text>' % (L - 8, py(yv) + 4, yv))
for xv in range(0, 51, 10):
    out.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="13" fill="#444">%d</text>' % (px(xv), H - B + 20, xv))
out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333"/><line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333"/>' % (L, T, L, H - B, L, H - B, W - R, H - B))
for name, ys, col, dash in series:
    pts = " ".join("%.1f,%.1f" % (px(x), py(y)) for x, y in zip(xs, ys))
    out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4" %s/>' % (pts, col, ('stroke-dasharray="%s"' % dash) if dash else ""))
lx = W - R - 150
for i, (name, _, col, dash) in enumerate(series):
    y = T + 18 + i * 22 + 150
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2.4" %s/><text x="%d" y="%d" font-size="13" fill="#222">%s</text>' % (lx, y, lx + 28, y, col, ('stroke-dasharray="%s"' % dash) if dash else "", lx + 36, y + 4, name))
out.append('<text x="%d" y="%d" text-anchor="middle" font-size="14" fill="#222">Epoch</text>' % ((L + W - R) // 2, H - 14))
out.append('<text transform="translate(18,%d) rotate(-90)" text-anchor="middle" font-size="14" fill="#222">Validation accuracy (%%)</text>' % ((T + H - B) // 2))
html = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="shot" content="03-科研绘图别只会让AI出PNG三类图三条路|01-screenshot-chart.png|600x470">
<style>body{margin:0;background:#fff;font-family:Arial,"DejaVu Sans","WenQuanYi Zen Hei",sans-serif}.c{padding:20px 20px 4px}.n{padding:0 20px 14px;font-size:12px;color:#999;text-align:right}</style></head>
<body><div class="c"><svg width="%d" height="%d" xmlns="http://www.w3.org/2000/svg" font-family="Arial, DejaVu Sans, sans-serif">%s</svg></div><div class="n">示意数据，非真实实验结果</div></body></html>""" % (W, H, "".join(out))
open(os.path.join(HERE, "截图源文件", "c1-chart.html"), "w", encoding="utf-8").write(html)
print("ok")
