#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HJ212-2017 环保监测数据传输协议报文解析器（Python 类库）

功能：
    1. is_valid_message        —— 报文格式合法性验证
    2. validate_crc            —— 基于 ANSI 标准（HJ212-2017 附录 A）的 CRC16 校验
    3. parse_data_segment      —— 数据段的结构化解析
    4. extract_monitoring_data —— 监测因子等核心数据的精准提取与封装

报文结构（HJ212-2017 第 6.3.1 节）：
    ## + 4位数据段长度（十进制） + 数据段 + 4位CRC校验值 + \r\n

CRC16 参数（HJ212-2017 附录 A，ANSI CRC16）：
    初始值：0xFFFF
    多项式：0xA001
    校验范围：仅数据段（不含包头 "##"、长度字段、CRC 字段与包尾 "\r\n"）
    校验码按先高字节后低字节的顺序存放（4 位十六进制表示）

    说明：实现严格对照标准附录 A 给出的 C 语言算法（CRC16_Checkout），
    并以标准附录 A 示例报文（CRC=1C80）实测验证通过。
"""

import re

HEADER = "##"
DATA_SEGMENT_LENGTH_DIGITS = 4
CRC_HEX_DIGITS = 4
CRC16_INIT_VALUE = 0xFFFF
CRC16_POLYNOMIAL = 0xA001

# 数据段内字段分隔符
FIELD_SEPARATOR = ";"
KEY_VALUE_SEPARATOR = "="
# CP 字段内数据区的起始/结束标记
CP_MARK = "&&"
# 监测因子属性分隔符，如 "a34002-Rtd"
FACTOR_ATTR_SEPARATOR = "-"


class HJ212Parser:
    """HJ212-2017 协议报文解析器。"""

    # ------------------------------------------------------------------
    # 1. 报文格式合法性验证
    # ------------------------------------------------------------------
    def is_valid_message(self, message: str) -> bool:
        """
        检查报文格式是否正确。

        合法报文需同时满足：
            1) 以 "##" 开头，并以 "\\r\\n" 结尾；
            2) 长度字段为 4 位十进制数字；
            3) 长度字段声明的长度与实际数据段 ASCII 字符数一致；
            4) 数据段包含协议必备字段 ST=、CN=、CP=（系统编码、命令编号、指令参数）；
            5) CRC 字段为 4 位十六进制数字。

        :param message: 原始报文（str）
        :return: 格式合法返回 True，否则返回 False
        """
        if not message or not isinstance(message, str):
            return False

        # 1) 报文头、报文尾
        if not message.startswith(HEADER):
            return False
        if not message.endswith("\r\n"):
            return False

        # 去掉 "##" 与 "\r\n" 后，剩余部分为：4位长度 + 数据段 + 4位CRC
        body = message[len(HEADER):-2]
        if len(body) <= DATA_SEGMENT_LENGTH_DIGITS + CRC_HEX_DIGITS:
            return False

        # 2) 长度字段必须为 4 位十进制数字
        length_field = body[:DATA_SEGMENT_LENGTH_DIGITS]
        if not length_field.isdigit():
            return False

        # 数据段与 CRC 字段
        data_segment = body[DATA_SEGMENT_LENGTH_DIGITS:-CRC_HEX_DIGITS]
        crc_field = body[-CRC_HEX_DIGITS:]

        # 3) 长度字段声明值与实际数据段长度一致
        declared_length = int(length_field)
        if declared_length != len(data_segment):
            return False

        # 4) 数据段应包含协议必备字段（系统编码、命令编号、指令参数）
        required_fields = ("ST=", "CN=", "CP=")
        if not all(field in data_segment for field in required_fields):
            return False

        # 5) CRC 字段必须为 4 位十六进制字符
        if not re.fullmatch(r"[0-9A-Fa-f]{4}", crc_field):
            return False

        return True

    # ------------------------------------------------------------------
    # 2. ANSI CRC16 校验
    # ------------------------------------------------------------------
    def _crc16_ansi(self, data: bytes) -> int:
        """
        计算 ANSI CRC16（HJ212-2017 附录 A 算法）。

        初始值 0xFFFF，多项式 0xA001；严格对照标准给出的 C 语言实现
        （每次先执行 (crc>>8) ^ byte，再进行 8 次移位与异或），
        经标准附录 A 示例报文实测验证（CRC=1C80）。

        :param data: 参与校验的数据段字节序列
        :return: 16 位 CRC 结果（int）
        """
        crc_reg = CRC16_INIT_VALUE
        for byte in data:
            crc_reg = (crc_reg >> 8) ^ byte
            for _ in range(8):
                check = crc_reg & 0x0001
                crc_reg >>= 1
                if check == 0x0001:
                    crc_reg ^= CRC16_POLYNOMIAL
        return crc_reg & 0xFFFF

    def validate_crc(self, message: str) -> bool:
        """
        校验报文的 CRC 值是否正确。

        校验范围：仅数据段（不含 "##"、长度字段、CRC 字段与 "\r\n"），
        将计算结果（4 位十六进制，高字节在前）与报文中的 CRC 字段比对。

        :param message: 原始报文（str）
        :return: CRC 校验通过返回 True，否则返回 False
        """
        if not self.is_valid_message(message):
            return False

        body = message[len(HEADER):-2]
        data_segment = body[DATA_SEGMENT_LENGTH_DIGITS:-CRC_HEX_DIGITS]
        crc_field = body[-CRC_HEX_DIGITS:]

        computed = self._crc16_ansi(data_segment.encode("ascii"))
        return "{:04X}".format(computed) == crc_field.upper()

    # ------------------------------------------------------------------
    # 3. 数据段结构化解析
    # ------------------------------------------------------------------
    def parse_data_segment(self, message: str) -> dict:
        """
        解析数据段，返回包含所有键值对的字典。

        数据段格式：QN=请求编号;ST=系统编码;CN=命令编号;PW=访问密码;
                    MN=监测点编号;Flag=标志位;CP=&&数据区&&

        :param message: 原始报文（str）
        :return: 键值对字典，例如
                 {"ST": "32", "CN": "2011", "PW": "123456",
                  "MN": "010000A8900016F000169DC0", "CP": "&&...&&"}
        :raises ValueError: 报文格式非法或数据段无法解析
        """
        if not self.is_valid_message(message):
            raise ValueError("报文格式非法，无法解析数据段")

        body = message[len(HEADER):-2]
        data_segment = body[DATA_SEGMENT_LENGTH_DIGITS:-CRC_HEX_DIGITS]

        result = {}
        fields = data_segment.split(FIELD_SEPARATOR)
        index = 0
        while index < len(fields):
            field = fields[index]
            if not field:
                index += 1
                continue
            if KEY_VALUE_SEPARATOR not in field:
                raise ValueError("数据段包含非法字段: {!r}".format(field))
            key, value = field.split(KEY_VALUE_SEPARATOR, 1)
            key = key.strip()
            if key == "CP":
                # CP 是最后一个字段，其数据区以 "&&" 包裹且内部同样使用 ";"
                # 分隔不同项目，因此命中 CP 后须将剩余片段合并为其值
                value = FIELD_SEPARATOR.join([value] + fields[index + 1:])
                result[key] = value.strip()
                break
            result[key] = value.strip()
            index += 1
        return result

    # ------------------------------------------------------------------
    # 4. 监测因子提取与封装
    # ------------------------------------------------------------------
    def _parse_cp_data(self, cp_value: str) -> dict:
        """
        解析 CP 字段中 && ... && 包裹的数据区。

        数据区中同一项目的不同分类值之间用逗号分隔，
        不同项目之间用分号分隔；每一项为 "字段名=值"。

        :param cp_value: CP 字段的原始值（含 && 包裹符）
        :return: 键值对字典（不含 && 包裹符）
        """
        inner = cp_value
        if inner.startswith(CP_MARK) and inner.endswith(CP_MARK):
            inner = inner[len(CP_MARK):-len(CP_MARK)]

        items = {}
        for block in inner.split(FIELD_SEPARATOR):
            if not block:
                continue
            # 一个数据块内可能有多个 "字段=值"，用逗号分隔
            for token in block.split(","):
                if KEY_VALUE_SEPARATOR not in token:
                    continue
                key, value = token.split(KEY_VALUE_SEPARATOR, 1)
                items[key.strip()] = value.strip()
        return items

    def extract_monitoring_data(self, message: str) -> dict:
        """
        从 CP 字段中提取所有监测因子及其数值。

        监测因子编码形如 "a34002"（烟气污染物）或 "A01001"（气象参数），
        其属性名以 "-" 连接（如 "-Rtd" 实时值、"-Flag" 状态标记）。
        本方法优先返回各因子的实时值（Rtd），无 Rtd 时返回首个属性值。

        :param message: 原始报文（str）
        :return: 监测因子字典，例如 {"a34002": "0.125", "a34041": "0.00"}
        """
        parsed = self.parse_data_segment(message)
        cp_value = parsed.get("CP", "")
        if not cp_value:
            return {}

        cp_items = self._parse_cp_data(cp_value)
        monitoring_data = {}
        for key, value in cp_items.items():
            if FACTOR_ATTR_SEPARATOR not in key:
                # DataTime、RtdInterval 等非监测因子字段跳过
                continue
            factor_code, attribute = key.rsplit(FACTOR_ATTR_SEPARATOR, 1)
            attribute = attribute.upper()
            # 优先记录实时值；已记录的因子仅当其出现 Rtd 时更新
            if factor_code not in monitoring_data or attribute == "RTD":
                monitoring_data[factor_code] = value
        return monitoring_data

    def describe(self, message: str) -> dict:
        """
        一键概览：对报文执行格式校验、CRC 校验、数据段解析与监测因子提取。

        :param message: 原始报文（str）
        :return: 包含全部解析结果的字典
        """
        return {
            "valid": self.is_valid_message(message),
            "crc_ok": self.validate_crc(message),
            "data_segment": self.parse_data_segment(message),
            "monitoring_data": self.extract_monitoring_data(message),
        }


def main() -> None:
    """命令行演示：解析 HJ212-2017 标准报文。"""
    # 标准附录 A 官方示例（CRC=1C80，已实测校验通过）
    sample = ("##0101QN=20160801085857223;ST=32;CN=1062;PW=100000;"
              "MN=010000A8900016F000169DC0;Flag=5;CP=&&RtdInterval=30&&"
              "1C80\r\n")

    parser = HJ212Parser()
    print("报文:", sample.strip())
    print("格式校验 is_valid_message   :", parser.is_valid_message(sample))
    print("CRC校验 validate_crc        :", parser.validate_crc(sample))
    print("数据段 parse_data_segment   :", parser.parse_data_segment(sample))
    print("监测因子 extract_monitoring :", parser.extract_monitoring_data(sample))


if __name__ == "__main__":
    main()
