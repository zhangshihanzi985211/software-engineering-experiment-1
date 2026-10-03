#!/usr/bin/env python3
"""WF 词频统计程序回归测试（第 0 步：字母频率统计）。"""
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))
WF_PY = os.path.join(BASE, "wf.py")


def run_wf(text):
    """以给定文本内容运行 wf.py，返回 (returncode, stdout)。"""
    fd, path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        proc = subprocess.run(
            [sys.executable, WF_PY, "-c", path],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        return proc.returncode, proc.stdout
    finally:
        os.unlink(path)


def letter_lines(out):
    """过滤出形如 `x:    12  33.33%` 的字母统计行（跳过表头行）。"""
    return [ln for ln in out.splitlines() if len(ln) >= 2 and ln[0].isalpha() and ln[1] == ":"]


class TestLetterFrequency(unittest.TestCase):
    def test_single_letter(self):
        code, out = run_wf("a" * 10)
        self.assertEqual(code, 0)
        self.assertIn("a:    10  100.00%", out)

    def test_case_insensitive_merge(self):
        # A(3)+a(2)=5, B(3)+b(2)=5，频率各 50%
        code, out = run_wf("AAAaaBBBbb")
        self.assertEqual(code, 0)
        self.assertIn("a:     5  50.00%", out)
        self.assertIn("b:     5  50.00%", out)

    def test_tie_breaks_by_dictionary_order(self):
        # S 与 T 频率相同（各 50%），S 应排在 T 之前
        code, out = run_wf("sStT")
        self.assertEqual(code, 0)
        s_idx = out.index("s:")
        t_idx = out.index("t:")
        self.assertLess(s_idx, t_idx)

    def test_descending_order(self):
        # e 出现 3 次最多，其次 o 2 次，最后 a 1 次
        code, out = run_wf("eoeoa")
        self.assertEqual(code, 0)
        e_idx = out.index("e:")
        o_idx = out.index("o:")
        a_idx = out.index("a:")
        self.assertLess(e_idx, o_idx)
        self.assertLess(o_idx, a_idx)

    def test_percentage_two_decimals(self):
        # a 1 次、b 1 次、c 1 次、d 1 次 → 各 25.00%
        code, out = run_wf("abcd")
        self.assertEqual(code, 0)
        self.assertIn("25.00%", out)

    def test_percentage_precision(self):
        # 2/3 → 66.67%（输出行：`a:     2  66.67%`）
        code, out = run_wf("aab")
        self.assertEqual(code, 0)
        self.assertIn("a:     2  66.67%", out)
        self.assertIn("b:     1  33.33%", out)

    def test_punctuation_and_whitespace_ignored(self):
        # 标点、数字、空白不计入统计，也不影响字母计数
        code, out = run_wf("a.,!? 123 a")
        self.assertEqual(code, 0)
        self.assertIn("a:     2  100.00%", out)

    def test_no_letters(self):
        code, out = run_wf("12345!@#$")
        self.assertEqual(code, 0)
        self.assertIn("没有 A-Z/a-z 字母", out)

    def test_empty_file(self):
        code, out = run_wf("")
        self.assertEqual(code, 0)
        self.assertIn("没有 A-Z/a-z 字母", out)

    def test_missing_argument(self):
        proc = subprocess.run(
            [sys.executable, WF_PY], capture_output=True, text=True,
            encoding="utf-8", timeout=30,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_whole_alphabet_sorted(self):
        # 26 个字母各 1 次：频率相同，全部按字典序输出，共 26 行
        code, out = run_wf("abcdefghijklmnopqrstuvwxyz")
        self.assertEqual(code, 0)
        lines = letter_lines(out)
        self.assertEqual(len(lines), 26)
        self.assertEqual(lines[0].startswith("a:"), True)
        self.assertEqual(lines[-1].startswith("z:"), True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
