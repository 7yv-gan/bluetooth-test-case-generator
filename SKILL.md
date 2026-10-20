***

name: bluetooth-test-case-generator

description: 为蓝牙连接功能（经典蓝牙 BR/EDR 与低功耗 BLE）生成企业级测试用例。当用户要求 “为蓝牙连接 / 扫描 / 配对 / 重连 / 数据传输功能编写、设计、生成、补充测试用例或测试点、评审蓝牙测试覆盖” 时使用。按功能、边界、异常、并发、安全、性能、兼容、体验 8 大维度生成，输出编号可追溯（TC - 模块 - 类型 - 序号）、优先级明确（P0-P3）的 Markdown 用例文档与 CSV/Excel 表格。



***

# 蓝牙连接测试用例生成器

## 概览

为蓝牙连接类功能生成一套结构化的企业级测试用例：先收集被测对象信息，再按覆盖清单确定维度，用内置场景库生成基线用例并扩展变体，最后输出 Markdown 文档 + CSV 表格并自检。

## 工作流

### Step 1 收集输入

向用户确认以下信息（缺失时使用默认值，不要反复追问）：



1. 被测产品名称（默认 “未命名产品”）

2. 主机平台：android /ios/pc /embedded（默认 android）

3. 蓝牙类型：ble /br-edr/dual（默认 ble）

4. 功能范围：扫描、配对、连接、断开、重连、数据传输、多连接等（默认全部）

5. 测试重点：回归 / 新增功能 / 专项（默认回归全量）

### Step 2 确定覆盖维度



* 默认覆盖 8 大维度：功能、边界、异常、并发、安全、性能、兼容、体验。

* 用户指定专项（如 “只测配对”）时缩小范围；涉及安全合规必须保留 SEC 维度。

* 生成前阅读 `references/coverage-checklist.md`，用其中的检查项作为覆盖基线。

### Step 3 生成用例



1. 先运行 `scripts/generate_test_cases.py` 生成基线用例集：



```
python scripts/generate_test_cases.py --product "产品名" --platform android --bt-type ble --out test_cases.csv --report test_cases.md
```

可用参数：`--modules SCAN,PAIR,CONN`（模块过滤）、`--dimensions FUN,BND`（维度过滤）、`--min-priority P1`（只保留 P0-P1）。



1. 依据 `references/bluetooth-domain.md` 扩展变体：对每个基线场景补充真实测试中会出现的变体（不同配对方式、不同异常前置、不同数据量）。

2. 新增用例必须符合 `references/test-case-schema.md` 的编号规则、优先级定义与字段模板；禁止自创编号格式。

### Step 4 输出交付



* 默认交付两个文件：Markdown 用例文档（分模块、带统计）+ CSV 表格（UTF-8 BOM，Excel 可直接打开）。

* 用户要求 Excel / 飞书表格时，加载 sheet skill 将 CSV 转为在线表格交付。

* 用户要求 Word 文档时，加载 word skill 按公文 / 文档格式排版交付。

### Step 5 自检

交付前逐项检查：



1. 用例 ID 全局唯一，编号符合规范（读 `references/test-case-schema.md` 复核）。

2. 优先级分布合理：P0 占 10–20%，P1 占 30–40%，其余 P2/P3。

3. 对照 `references/coverage-checklist.md` 逐项打勾，未覆盖的维度补充用例。

4. 每条用例：单一验证点、步骤可操作、预期结果可判定。

5. 向用户说明：共生成 N 条用例、覆盖哪些维度、输出文件路径。

## 资源导航



| 资源                                 | 何时读取                           |
| ---------------------------------- | ------------------------------ |
| `references/bluetooth-domain.md`   | 生成用例前：了解连接状态机、配对方式、典型缺陷模式      |
| `references/coverage-checklist.md` | Step 2 确定维度、Step 5 自检覆盖        |
| `references/test-case-schema.md`   | 编写 / 扩展 / 评审用例时：编号、优先级、字段、质量标准 |
| `scripts/generate_test_cases.py`   | Step 3 直接运行，不需要读入上下文           |

## 改造为其他功能域（可选）

本 skill 的场景库集中在 `scripts/generate_test_cases.py` 的 `SCENARIOS` 列表。改造成其他功能域（如 API 接口、登录、支付）时：



1. 复制整个 skill 目录，重命名（如 `api-test-case-generator`）。

2. 替换 `SCENARIOS` 中的场景为对应领域的真实场景（模块码、类型码、步骤、预期）。

3. 重写 `references/bluetooth-domain.md` 为对应领域的领域知识。

4. 重写 `references/coverage-checklist.md` 的检查项。

5. 保留 `references/test-case-schema.md`（编号 / 优先级 / 字段规范可复用）与工作流不变。