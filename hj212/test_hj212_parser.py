#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HJ212Parser 单元测试

运行方式：
    python3 -m unittest test_hj212_parser -v
    或
    python3 test_hj212_parser.py
"""

import unittest

from hj212_parser import HJ212Parser, HEADER, CRC_HEX_DIGITS, DATA_SEGMENT_LENGTH_DIGITS

# HJ212-2017 附录 A 官方示例报文（CRC=1C80，与标准算法实测一致）
OFFICIAL_SAMPLE = (
    "##0101QN=20160801085857223;ST=32;CN=1062;PW=100000;"
    "MN=010000A8900016F000169DC0;Flag=5;CP=&&RtdInterval=30&&"
    "1C80\r\n"
)


def build_message(data_segment: str) -> str:
    """
    构造一条 CRC 正确的 HJ212 报文，供往返校验测试使用。
    按协议：长度=数据段 ASCII 字符数（4 位十进制补齐），
    CRC 对数据段按附录 A 算法计算（4 位十六进制）。
    """
    parser = HJ212Parser()
    length_field = "{:04d}".format(len(data_segment))
    crc = parser._crc16_ansi(data_segment.encode("ascii"))
    return HEADER + length_field + data_segment + "{:04X}".format(crc) + "\r\n"


class TestIsValidMessage(unittest.TestCase):

    def setUp(self):
        self.parser = HJ212Parser()

    def test_official_sample_is_valid(self):
        self.assertTrue(self.parser.is_valid_message(OFFICIAL_SAMPLE))

    def test_missing_header(self):
        self.assertFalse(self.parser.is_valid_message(OFFICIAL_SAMPLE[2:]))

    def test_missing_crlf(self):
        self.assertFalse(self.parser.is_valid_message(OFFICIAL_SAMPLE[:-2]))

    def test_length_field_not_digits(self):
        bad = OFFICIAL_SAMPLE.replace("##0101", "##ABCD", 1)
        self.assertFalse(self.parser.is_valid_message(bad))

    def test_length_mismatch(self):
        bad = OFFICIAL_SAMPLE.replace("##0101", "##0102", 1)
        self.assertFalse(self.parser.is_valid_message(bad))

    def test_crc_field_not_hex(self):
        bad = OFFICIAL_SAMPLE.replace("1C80", "ZZZZ", 1)
        self.assertFalse(self.parser.is_valid_message(bad))

    def test_empty_message(self):
        self.assertFalse(self.parser.is_valid_message(""))


class TestValidateCrc(unittest.TestCase):

    def setUp(self):
        self.parser = HJ212Parser()

    def test_official_sample_crc_ok(self):
        self.assertTrue(self.parser.validate_crc(OFFICIAL_SAMPLE))

    def test_tampered_data_crc_fails(self):
        tampered = OFFICIAL_SAMPLE.replace("RtdInterval=30", "RtdInterval=60", 1)
        self.assertFalse(self.parser.validate_crc(tampered))

    def test_wrong_crc_value_fails(self):
        wrong_crc = OFFICIAL_SAMPLE.replace("1C80", "0000", 1)
        self.assertFalse(self.parser.validate_crc(wrong_crc))

    def test_round_trip_generated_message(self):
        data_segment = (
            "ST=21;CN=2011;PW=123456;MN=010000A8900016F000169DC0;"
            "CP=&&DataTime=20240101000000;a34000-Rtd=12.34,a34000-Flag=N;"
            "A01001-Rtd=23.5,A01001-Flag=N&&"
        )
        message = build_message(data_segment)
        self.assertTrue(self.parser.is_valid_message(message))
        self.assertTrue(self.parser.validate_crc(message))


class TestParseDataSegment(unittest.TestCase):

    def setUp(self):
        self.parser = HJ212Parser()

    def test_parse_official_sample(self):
        parsed = self.parser.parse_data_segment(OFFICIAL_SAMPLE)
        self.assertEqual(parsed["QN"], "20160801085857223")
        self.assertEqual(parsed["ST"], "32")
        self.assertEqual(parsed["CN"], "1062")
        self.assertEqual(parsed["PW"], "100000")
        self.assertEqual(parsed["MN"], "010000A8900016F000169DC0")
        self.assertEqual(parsed["Flag"], "5")
        self.assertEqual(parsed["CP"], "&&RtdInterval=30&&")

    def test_parse_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.parser.parse_data_segment("not-a-message\r\n")


class TestExtractMonitoringData(unittest.TestCase):

    def setUp(self):
        self.parser = HJ212Parser()

    def test_extract_monitoring_factors(self):
        data_segment = (
            "ST=21;CN=2011;PW=123456;MN=010000A8900016F000169DC0;"
            "CP=&&DataTime=20240101000000;a34000-Rtd=12.34,a34000-Flag=N;"
            "A01001-Rtd=23.5,A01001-Flag=N&&"
        )
        message = build_message(data_segment)
        data = self.parser.extract_monitoring_data(message)
        self.assertEqual(data.get("a34000"), "12.34")
        self.assertEqual(data.get("A01001"), "23.5")

    def test_extract_skips_non_factor_fields(self):
        # 官方示例中 CP 只有 RtdInterval，不包含监测因子
        self.assertEqual(self.parser.extract_monitoring_data(OFFICIAL_SAMPLE), {})

    def test_extract_raises_without_cp(self):
        # 缺少必备字段 CP 的报文属于格式非法，解析应抛出 ValueError
        data_segment = "ST=21;CN=2011;PW=123456;MN=1234567890ABCDEF"
        message = build_message(data_segment)
        with self.assertRaises(ValueError):
            self.parser.extract_monitoring_data(message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
