#!/usr/bin/env python3
"""把文章里的本地图片路径换成图床链接,生成可直接粘进 WeMD 的 article_公众号版.md。

步骤:
 1. 把文章文件夹里 imgs/ 下的图片上传到你的图床(WeMD 里配置的图床,或任何图床),拿到链接。
 2. 写一个映射文件 links.json,例如:
        {"fig1.png": "https://你的图床/xxx/fig1.png"}
    键是图片文件名(也可以写成 imgs/fig1.png)。
 3. 运行:  python3 replace_image_urls.py 文章文件夹 links.json
原来的 article.md 不会被改动。
"""
import json
import os
import re
import sys


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    folder, mapfile = sys.argv[1], sys.argv[2]
    with open(mapfile, encoding="utf-8") as f:
        links = json.load(f)
    links = {os.path.basename(k): v for k, v in links.items()}
    src = os.path.join(folder, "article.md")
    with open(src, encoding="utf-8") as f:
        text = f.read()
    missing = []

    def sub(m):
        name = os.path.basename(m.group(2))
        if name in links:
            return "![%s](%s)" % (m.group(1), links[name])
        missing.append(name)
        return m.group(0)

    out = re.sub(r"!\[([^\]]*)\]\((imgs/[^)]+)\)", sub, text)
    dst = os.path.join(folder, "article_公众号版.md")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)
    print("已生成:" + dst)
    if missing:
        print("以下图片没有对应链接,保持原样:" + ", ".join(sorted(set(missing))))


if __name__ == "__main__":
    main()
