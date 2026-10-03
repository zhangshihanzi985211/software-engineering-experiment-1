#!/usr/bin/env python3
"""WF (Word Frequency) 词频统计程序 —— 第 0 步：字母频率统计。

用法：
    python3 wf.py -c <file name>

功能：
    输出指定英文文本文件中 26 个字母（A-Z/a-z）出现的频率，由高到低排列，
    并显示字母出现的百分比（精确到小数点后两位）；若两个字母频率相同，
    则按字典序（字母序）排列。

    字母频率 = 该字母出现次数 / 所有 A-Z、a-z 字母出现的总数（不区分大小写）。
"""
import argparse
from collections import Counter


def count_letters(text: str) -> Counter:
    """统计 A-Z/a-z 各字母出现次数（大小写不敏感，统一归为小写）。"""
    counter = Counter()
    for ch in text:
        if "a" <= ch <= "z":
            counter[ch] += 1
        elif "A" <= ch <= "Z":
            counter[ch.lower()] += 1
    return counter


def format_output(counts: Counter, total: int) -> str:
    """按 频率由高到低、同频按字典序 生成输出文本。"""
    lines = []
    for ch in sorted(counts, key=lambda x: (-counts[x], x)):
        pct = counts[ch] / total * 100
        lines.append(f"{ch}: {counts[ch]:5d}  {pct:5.2f}%")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WF (Word Frequency) 字母频率统计（第 0 步）"
    )
    parser.add_argument("-c", metavar="FILE", required=True,
                        help="英文文本文件路径")
    args = parser.parse_args()

    with open(args.c, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    counts = count_letters(text)
    total = sum(counts.values())
    if total == 0:
        print("文件中没有 A-Z/a-z 字母。")
        return 0
    print(f"字母总数为：{total}")
    print(format_output(counts, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
