#!/usr/bin/env python3
"""用 check_refs.py 配合模拟的 Crossref 返回，生成第 04 篇的两张截图源文件。
(运行环境访问不了真实接口。如果你本机能连 Crossref，可以去掉 opener 参数，用真实结果重做截图。)"""
import contextlib, csv, html, importlib.util, io, json, os, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(HERE, "..", "04-用脚本揪出参考文献里的幽灵论文")
spec = importlib.util.spec_from_file_location("cr", os.path.join(FOLDER, "check_refs.py"))
cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)

CANNED = [
    ("Deep Residual Learning for Image Recognition", "10.1109/CVPR.2016.90"),
    ("Deep learning", "10.1038/nature14539"),
    ("Cross-domain transfer learning in quantum dot arrays", "10.1000/demo.0003"),
]
calls = []
class R(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): pass
def opener(req, timeout=0):
    t, d = CANNED[len(calls)]; calls.append(1)
    return R(json.dumps({"message": {"items": [{"title": [t], "DOI": d}]}}).encode())

tmp = tempfile.mkdtemp()
refs = os.path.join(tmp, "refs.txt")
open(refs, "w", encoding="utf-8").write(open(os.path.join(FOLDER, "refs_示例.txt"), encoding="utf-8").read())
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    cr.main([refs], opener=opener, sleep=lambda s: None)
out = buf.getvalue().replace(os.path.join(tmp, "refs_result.csv"), "refs_result.csv")

def colour(line):
    e = html.escape(line)
    for word, cls in (("基本可信", "ok"), ("未找到匹配", "bad"), ("存疑", "warn")):
        e = e.replace(word, '<span class="%s">%s</span>' % (cls, word))
    return e
body = "\n".join(colour(l) for l in out.strip("\n").split("\n"))
open(os.path.join(HERE, "截图源文件", "s04-terminal.html"), "w", encoding="utf-8").write("""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="shot" content="04-用脚本揪出参考文献里的幽灵论文|shot-terminal.png|980x450">
<style>
body{margin:0;background:#1b1e27;font-family:"DejaVu Sans Mono","WenQuanYi Zen Hei",monospace;color:#d6dcec}
.win{margin:20px;border-radius:10px;overflow:hidden;background:#232733;box-shadow:0 8px 30px rgba(0,0,0,.45)}
.bar{background:#171a22;padding:10px 14px;display:flex;gap:8px;align-items:center;font-size:13px;color:#7d869b;font-family:"WenQuanYi Zen Hei",sans-serif}
.d{width:12px;height:12px;border-radius:50%}
pre{margin:0;padding:18px 22px 22px;font-size:14.5px;line-height:1.7;white-space:pre-wrap}
.p{color:#7cc7ff}.ok{color:#7ddc9a}.bad{color:#ff7b7b}.warn{color:#ffc857}
</style></head><body><div class="win">
<div class="bar"><span class="d" style="background:#ff5f56"></span><span class="d" style="background:#ffbd2e"></span><span class="d" style="background:#27c93f"></span><span style="margin-left:12px">终端（演示数据，第 3 条为虚构文献）</span></div>
<pre><span class="p">$</span> python check_refs.py refs.txt

@@X@@</pre></div></body></html>""".replace("@@X@@", body))

rows = list(csv.reader(open(os.path.join(tmp, "refs_result.csv"), encoding="utf-8-sig")))
def cell(c, i, r):
    cls = ""
    if i == 1 and r:
        cls = ' class="%s"' % ("ok" if c == "基本可信" else "bad")
    return "<td%s>%s</td>" % (cls, html.escape(c))
trs = "<tr>%s</tr>" % "".join("<th>%s</th>" % html.escape(c) for c in rows[0][:5])
for r in rows[1:]:
    trs += "<tr>%s</tr>" % "".join(cell(c, i, True) for i, c in enumerate(r[:5]))
open(os.path.join(HERE, "截图源文件", "s04-csv.html"), "w", encoding="utf-8").write("""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="shot" content="04-用脚本揪出参考文献里的幽灵论文|shot-csv.png|1000x215">
<style>
body{margin:0;background:#fff;font-family:"WenQuanYi Zen Hei","Noto Sans CJK SC",sans-serif;color:#222}
.t{background:#217346;color:#fff;font-size:14px;padding:9px 16px}
table{border-collapse:collapse;width:100%;font-size:15px}
th{background:#f0f2f5;font-weight:normal;color:#555;text-align:left}
th,td{border:1px solid #d6d9df;padding:10px 12px}
td{background:#fff}.ok{color:#1f8f4e}.bad{color:#d33;background:#fff0f0}
.s{padding:8px 16px;background:#f7f7f7;border-top:1px solid #ddd;color:#888;font-size:13px}
</style></head><body><div class="t">refs_result.csv（演示数据，序号 3 为虚构文献）</div>
<table>@@X@@</table><div class="s">用 Excel 或 WPS 打开，按“判断”这一列筛选即可</div></body></html>""".replace("@@X@@", trs))
print(out)
