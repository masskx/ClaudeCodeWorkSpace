#!/usr/bin/env python3
"""批量检查参考文献是否真实存在(基于 Crossref 免费 API,无需注册)。

用法:
    python3 check_refs.py refs.txt                # refs.txt 每行一条参考文献(含标题即可)
    python3 check_refs.py refs.txt -m you@xx.com  # 建议留邮箱,Crossref 会给"礼貌通道"
结果同时打印到屏幕,并保存为 refs_result.csv。

注意:Crossref 没有收录所有文献(arXiv 预印本、很多中文文献、部分图书都可能查不到)。
所以"未找到"只代表"需要人工复核",不等于"造假"。
"""
import argparse
import csv
import difflib
import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.crossref.org/works"


def norm(s):
    return re.sub(r"[\W_]+", " ", s.lower()).strip()


def similarity(a, b):
    """标题相似度:整体相似度与"查询里是否包含候选标题"取较大值。"""
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    contain = 1.0 if b in a else 0.0
    return max(ratio, contain)


def query_crossref(ref, mailto=None, opener=urllib.request.urlopen):
    params = {"query.bibliographic": ref, "rows": 1}
    if mailto:
        params["mailto"] = mailto
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "ref-checker/1.0"})
    with opener(req, timeout=20) as resp:
        data = json.load(resp)
    items = data.get("message", {}).get("items", [])
    return items[0] if items else None


def judge(ref, item):
    if not item:
        return "未找到", "", "", 0.0
    title = (item.get("title") or [""])[0]
    doi = item.get("DOI", "")
    score = similarity(ref, title)
    if score >= 0.85:
        level = "基本可信"
    elif score >= 0.55:
        level = "存疑(请人工看一眼)"
    else:
        level = "未找到匹配"
    return level, title, doi, score


def main(argv=None, opener=urllib.request.urlopen, sleep=time.sleep):
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("-m", "--mailto", default=None)
    args = ap.parse_args(argv)
    with open(args.file, encoding="utf-8") as f:
        refs = [ln.strip() for ln in f if ln.strip()]
    rows = []
    for i, ref in enumerate(refs, 1):
        try:
            item = query_crossref(ref, args.mailto, opener)
            level, title, doi, score = judge(ref, item)
        except Exception as e:  # 网络错误等
            level, title, doi, score = "查询失败(%s)" % type(e).__name__, "", "", 0.0
        rows.append([i, level, "%.2f" % score, title, doi, ref])
        print("[%d/%d] %s  相似度 %.2f\n    原文:%s\n    匹配:%s  DOI:%s" % (i, len(refs), level, score, ref[:80], title[:80], doi))
        sleep(1)  # 对免费 API 保持礼貌
    out = re.sub(r"\.\w+$", "", args.file) + "_result.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["序号", "判断", "相似度", "Crossref 标题", "DOI", "你的参考文献"])
        w.writerows(rows)
    print("\n已保存:" + out)
    bad = [r for r in rows if not r[1].startswith("基本可信")]
    print("需要人工复核的条目:%d / %d" % (len(bad), len(rows)))


if __name__ == "__main__":
    sys.exit(main())
