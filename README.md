# 软件工程实验一：个人编程技能和 git 操作

本仓库是《软件工程》课程实验一的源码与文档，用于练习个人代码管理与 git 基本操作，
并完成两项编程任务：

1. 使用熟悉的编程语言输出 `Hello World`；
2. 利用 AI 辅助编程，实现 **HJ212-2017 环保协议报文解析 Python 类库**。

## 仓库结构

```
software-engineering-experiment-1
├── README.md                     # 本说明文件
├── hello_world
│   ├── hello_world.py            # Hello World（Python 版本）
│   └── hello_world.c             # Hello World（C 语言版本）
├── hj212
│   ├── hj212_parser.py           # HJ212Parser 协议解析类库
│   └── test_hj212_parser.py      # 单元测试（16 个用例）
└── docs
    └── 读后感.md                 # 任正非公开信读后感
```

## 运行方法

```bash
# Hello World（Python）
python3 hello_world/hello_world.py

# Hello World（C 语言）
gcc hello_world/hello_world.c -o hello_world && ./hello_world

# HJ212 解析器演示
python3 hj212/hj212_parser.py

# HJ212 解析器单元测试
python3 -m unittest hj212/test_hj212_parser.py -v
# 或
cd hj212 && python3 test_hj212_parser.py
```

## HJ212Parser 功能说明

| 方法 | 功能 |
| --- | --- |
| `is_valid_message(message)` | 报文格式合法性验证（包头/包尾、长度字段、数据段必备字段、CRC 字段） |
| `validate_crc(message)` | ANSI CRC16 校验（HJ212-2017 附录 A，初始值 0xFFFF，多项式 0xA001） |
| `parse_data_segment(message)` | 数据段结构化解析，返回全部键值对字典 |
| `extract_monitoring_data(message)` | 从 CP 字段提取监测因子及其数值 |

**报文结构**（HJ 212-2017 第 6.3.1 节）：

```
## + 4位数据段长度（十进制） + 数据段 + 4位CRC校验值 + \r\n
```

**CRC16 校验规则**：
- 算法：ANSI CRC16（初始值 0xFFFF，多项式 0xA001），实现与标准附录 A 的 C 语言代码一致；
- 校验范围：仅数据段（不含包头 `##`、长度字段、CRC 字段与包尾 `\r\n`）；
- 标准附录 A 官方示例 `##0101QN=...;CP=&&RtdInterval=30&&1C80\r\n` 已通过 `validate_crc` 实测验证。

## 参考规范

- HJ 212-2017《污染物在线监控（监测）系统数据传输标准》（生态环境部发布）
- 编程规范参考《阿里巴巴 Java 开发手册》之编程规约（注释、命名、健壮性）
- Git 提交注释遵循 Conventional Commits 规范（`feat` / `fix` / `docs` / `test` 等）

## 测试结果

```
Ran 16 tests in 0.001s
OK
```
