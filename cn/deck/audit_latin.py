# -*- coding: utf-8 -*-
r"""审计中文正文: 出现的每一个拉丁词, 必须属于白名单(含复数) 或是某张卡的牌名。
白名单与渲染器 TERMS / RULE_TERMS 保持一致; 牌名允许出现是因为正文会点名别的牌。
用法: python cn\deck\audit_latin.py
"""
import csv
import io
import os
import re
from collections import defaultdict

ROOT = r"D:\wenje-ma\isaac-four-souls"

TERMS = (
    "loot", "hp", "atk", "dice", "tap", "soul", "treasure", "damage", "room",
    "boss", "dc", "eternal", "counter", "ability", "reward", "item", "curse",
    "trinket", "ambush", "guppy", "indomitable",
)
RULE_TERMS = (
    "start phase", "action phase", "end phase", "slot", "crowd slot",
    "purchase", "death", "win", "stack", "priority",
)

TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9'’\-]*")


def forms(term):
    out = {term}
    if " " in term:
        return out
    if term.endswith("y"):
        out.add(term[:-1] + "ies")
    elif term.endswith(("s", "x", "z", "ch", "sh")):
        out.add(term + "es")
    else:
        out.add(term + "s")
    return out


def main():
    allowed = set()
    for t in TERMS + RULE_TERMS:
        allowed |= forms(t)
    allowed |= {"d6", "d8", "d10", "d12"}

    # 正文会点名别的牌, 牌名(整名与其中的每个词)都算合法
    # x = 变量; track = 阶梯卡的牌名; 下面几个是被引用但不在本套数据里的牌名
    name_words = {"x", "track", "ultra", "flesh", "kid", "harbingers"}
    for r in csv.DictReader(io.open(os.path.join(ROOT, "en", "data", "cards_final.csv"), encoding="utf-8")):
        n = (r.get("name") or "").strip()
        if n:
            name_words.add(n.lower())
            name_words |= {w.lower() for w in re.findall(r"[A-Za-z]+", n)}
    names = name_words

    rows = list(csv.DictReader(io.open(os.path.join(ROOT, "cn", "data", "translations.csv"), encoding="utf-8")))
    bad = defaultdict(lambda: {"n": 0, "cards": []})
    good = defaultdict(int)

    for r in rows:
        zh = (r.get("effect_cn") or "").replace("\\n", "\n")
        if not zh.strip():
            continue
        for m in TOKEN.finditer(zh):
            tok = m.group(0).rstrip("-'")
            low = tok.lower()
            bare = low.replace("'s", "").replace("'", "")
            if low in allowed or bare in allowed:
                good[low] += 1
            elif low in names or bare in names:
                good["<name:%s>" % low] += 1
            else:
                bad[tok]["n"] += 1
                if len(bad[tok]["cards"]) < 3:
                    bad[tok]["cards"].append(r.get("slug", ""))

    print("白名单+牌名 命中 %d 种, 违规 %d 种" % (len(good), len(bad)))
    if bad:
        print("\n违规词 (出现次数 / 示例卡):")
        for tok, d in sorted(bad.items(), key=lambda kv: -kv[1]["n"]):
            print("  %-14s %3d   %s" % (tok, d["n"], ", ".join(d["cards"])))

    print("\n白名单里在正文中出现过 0 次的词 (规则卡却说它, 就是死引用):")
    used = {k for k in good if not k.startswith("<name:")}
    for t in TERMS + RULE_TERMS:
        if not (forms(t) & used):
            print("  %s" % t)


if __name__ == "__main__":
    main()
