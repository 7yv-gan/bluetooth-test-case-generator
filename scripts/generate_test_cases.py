# -*- coding: utf-8 -*-
"""Bluetooth connectivity test case generator (enterprise-grade).

Generates a deterministic, auditable test case suite for Bluetooth
(BR/EDR and BLE) connectivity features. The scenario library embedded below
covers 8 quality dimensions: functional, boundary, exception, concurrency,
security, performance, compatibility, experience.

Usage:
    python generate_test_cases.py \
        --product "智能手环X1" \
        --platform android \
        --bt-type ble \
        --modules SCAN,PAIR,CONN,DISC,RECON,DATA,MULTI,SEC,PERF,COMPAT \
        --dimensions FUN,BND,EXC,CON,SEC,PERF,COMPAT,EXP \
        --min-priority P3 \
        --out test_cases.csv \
        --report test_cases.md

Outputs:
    - CSV (UTF-8 with BOM, Excel friendly)
    - Markdown report grouped by module with coverage stats
"""

import argparse
import csv
import json
import sys
from collections import Counter

# ---------------------------------------------------------------------------
# Scenario library: module code, type code, title, priority, preconditions,
# test data, steps, expected results, notes.
# ---------------------------------------------------------------------------

SCENARIOS = [
    # ---- Functional (FUN) ------------------------------------------------
    dict(module="SCAN", type="FUN", title="开启扫描后能发现目标设备", priority="P0",
         preconditions="1) 手机蓝牙已开启；2) 目标设备处于可发现状态并持续广播",
         data="目标设备名称",
         steps=["打开应用进入设备列表页，触发扫描",
                "等待扫描完成（默认扫描时长）",
                "在结果列表中查找目标设备"],
         expected=["扫描列表显示目标设备名称",
                   "列表中展示信号强度/RSSI 或距离指示",
                   "扫描结果可刷新、可停止"],
         notes="核心主流程"),
    dict(module="SCAN", type="FUN", title="设备可发现性开关切换生效", priority="P2",
         preconditions="目标设备支持可发现性开关",
         data="",
         steps=["关闭目标设备可发现性，手机发起扫描",
                "开启目标设备可发现性，手机再次扫描"],
         expected=["关闭状态下扫描列表不出现该设备",
                   "开启后可正常发现"],
         notes=""),
    dict(module="PAIR", type="FUN", title="Just Works 方式完成配对", priority="P1",
         preconditions="1) 目标设备无输入输出能力；2) 处于可发现状态",
         data="",
         steps=["手机发起扫描并选择目标设备",
                "触发配对，等待系统完成 Just Works 配对",
                "确认设备出现在已配对列表"],
         expected=["配对无需用户输入即可完成",
                   "设备出现在已配对列表，应用显示已连接"],
         notes=""),
    dict(module="PAIR", type="FUN", title="Passkey Entry 方式完成配对并绑定", priority="P0",
         preconditions="1) 手机与设备均支持 Passkey；2) 设备可被发现",
         data="PIN=123456",
         steps=["手机扫描并选择目标设备发起配对",
                "手机弹出 PIN 输入框时输入 123456 并确认",
                "等待配对完成",
                "断开连接后再次连接"],
         expected=["配对成功，设备进入已配对列表",
                   "再次连接无需重新配对（绑定生效）"],
         notes="关联需求 BLE-REQ-012"),
    dict(module="PAIR", type="FUN", title="Numeric Comparison 双方确认完成配对", priority="P1",
         preconditions="手机与设备均有屏幕显示能力",
         data="6 位确认码",
         steps=["发起配对，双方显示 6 位数字",
                "核对两边数字一致并确认",
                "等待配对完成"],
         expected=["数字一致确认后配对成功",
                   "数字不一致时可拒绝，配对不建立"],
         notes=""),
    dict(module="PAIR", type="FUN", title="解除绑定（取消配对）", priority="P1",
         preconditions="设备已配对并绑定",
         data="",
         steps=["在已配对列表中删除目标设备（解除配对）",
                "再次发起连接"],
         expected=["解除后设备从已配对列表移除",
                   "再次连接需要重新走配对流程"],
         notes=""),
    dict(module="CONN", type="FUN", title="正常建立连接", priority="P0",
         preconditions="设备已配对",
         data="",
         steps=["在应用内点击目标设备发起连接",
                "等待连接建立"],
         expected=["应用显示'连接中'状态",
                   "连接成功后显示'已连接'，连接状态可读取"],
         notes="核心主流程"),
    dict(module="DISC", type="FUN", title="用户主动断开连接", priority="P1",
         preconditions="设备处于已连接状态",
         data="",
         steps=["在应用内触发断开操作"],
         expected=["应用显示'已断开'状态",
                   "设备端同步断开，可再次发起连接"],
         notes=""),
    dict(module="RECON", type="FUN", title="断线后自动重连成功", priority="P0",
         preconditions="1) 设备已连接且已绑定；2) 支持自动重连策略",
         data="",
         steps=["连接设备后，使设备离开范围导致断线",
                "将设备带回范围，等待自动重连",
                "观察连接状态变化"],
         expected=["断线时应用提示'连接已断开'",
                   "设备回到范围内后自动重连成功，无需用户操作"],
         notes="核心主流程"),
    dict(module="RECON", type="FUN", title="手动重连", priority="P1",
         preconditions="设备已配对，当前未连接",
         data="",
         steps=["在设备列表点击已配对设备发起手动连接"],
         expected=["连接成功，恢复数据传输"],
         notes=""),
    dict(module="DATA", type="FUN", title="双向数据传输正常", priority="P0",
         preconditions="设备已连接，数据通道可用",
         data="上行数据包 10KB，下行数据包 10KB",
         steps=["应用向设备发送上行数据包",
                "设备向应用发送下行数据包",
                "校验两端收到的数据完整性"],
         expected=["上行数据被设备完整接收",
                   "下行数据被应用完整接收，内容一致无丢失"],
         notes="核心主流程"),
    dict(module="MULTI", type="FUN", title="多设备同时连接", priority="P1",
         preconditions="产品支持多连接，至少有 2 台目标设备",
         data="",
         steps=["依次连接设备 A、设备 B",
                "分别与 A、B 交互数据"],
         expected=["两台设备均保持已连接",
                   "与 A、B 的数据交互互不干扰"],
         notes=""),
    # ---- Boundary (BND) ---------------------------------------------------
    dict(module="CONN", type="BND", title="临界距离下连接稳定", priority="P2",
         preconditions="开阔环境，可测量距离",
         data="距离 8-10 米（BLE 典型边界）",
         steps=["将设备置于正常距离连接成功",
                "逐步拉开至临界距离，持续交互数据"],
         expected=["临界距离下连接保持，无掉线",
                   "数据交互仍可完成（允许时延增大）"],
         notes=""),
    dict(module="CONN", type="BND", title="超出射频范围后连接断开", priority="P1",
         preconditions="设备已连接",
         data="",
         steps=["连接设备后将设备移动到超出射频范围（>15 米或隔墙）"],
         expected=["连接在超时参数内断开并提示",
                   "回到范围内可恢复连接"],
         notes=""),
    dict(module="CONN", type="BND", title="设备低电量时连接行为", priority="P2",
         preconditions="设备电量处于低电量档（如 5%-10%）",
         data="",
         steps=["低电量状态下发起扫描和连接",
                "观察连接成功后的数据传输"],
         expected=["低电量下仍可连接或给出明确提示",
                   "不得出现反复断连、数据丢失"],
         notes=""),
    dict(module="CONN", type="BND", title="达到连接数上限后再连接", priority="P1",
         preconditions="产品有明确连接数上限（如最多 1 台）",
         data="",
         steps=["已连接设备 A，尝试连接设备 B"],
         expected=["系统拒绝新连接或自动断开 A，行为与产品定义一致",
                   "对用户有明确提示"],
         notes=""),
    dict(module="SCAN", type="BND", title="扫描超时参数边界", priority="P2",
         preconditions="支持配置扫描超时",
         data="扫描超时=最小值",
         steps=["设置扫描超时为最小值并发起扫描"],
         expected=["扫描在超时时间到达后正常结束，不崩溃不卡死",
                   "可再次发起扫描"],
         notes=""),
    dict(module="DATA", type="BND", title="MTU 边界与超长数据包", priority="P2",
         preconditions="设备已连接",
         data="单包=MTU 协商值；超长包=MTU×2",
         steps=["发送等于 MTU 的单包",
                "发送超过 MTU 的大包"],
         expected=["MTU 大小数据包完整传输",
                   "超长包被正确分片/重组，或按协议明确报错，不丢数据"],
         notes=""),
    # ---- Exception (EXC) ---------------------------------------------------
    dict(module="CONN", type="EXC", title="蓝牙关闭状态下发起连接", priority="P1",
         preconditions="手机蓝牙处于关闭状态",
         data="",
         steps=["蓝牙关闭时打开应用发起扫描/连接"],
         expected=["应用提示需开启蓝牙，不崩溃",
                   "开启蓝牙后可正常扫描连接"],
         notes=""),
    dict(module="CONN", type="EXC", title="飞行模式下的连接行为", priority="P1",
         preconditions="设备已配对",
         data="",
         steps=["开启飞行模式后尝试连接",
                "关闭飞行模式后重试"],
         expected=["飞行模式下连接失败并有提示",
                   "关闭飞行模式后可正常连接"],
         notes=""),
    dict(module="CONN", type="EXC", title="对端设备关机/断电", priority="P1",
         preconditions="设备已连接",
         data="",
         steps=["连接状态下直接关闭目标设备电源"],
         expected=["应用感知连接断开并给出提示",
                   "重新开机后恢复连接流程正常"],
         notes=""),
    dict(module="CONN", type="EXC", title="对端离开范围后恢复", priority="P2",
         preconditions="设备已连接",
         data="",
         steps=["将设备移出范围导致断线",
                "将设备带回范围"],
         expected=["断线提示明确",
                   "带回范围内后自动重连或可手动重连成功"],
         notes=""),
    dict(module="PAIR", type="EXC", title="配对过程中用户取消", priority="P1",
         preconditions="配对进行中",
         data="",
         steps=["发起配对后，在弹出确认框时点击取消"],
         expected=["配对流程中止，无残留状态",
                   "设备不进入已配对列表，可再次发起配对"],
         notes=""),
    dict(module="SCAN", type="EXC", title="定位权限被拒绝时扫描行为", priority="P1",
         preconditions="Android 设备，定位权限未授予",
         data="",
         steps=["拒绝定位权限后打开应用发起扫描"],
         expected=["应用提示权限不足或引导开启权限",
                   "授权后可正常扫描"],
         notes=""),
    dict(module="RECON", type="EXC", title="系统重启/应用崩溃后恢复连接", priority="P2",
         preconditions="设备已绑定",
         data="",
         steps=["连接状态下重启手机",
                "重启后打开应用"],
         expected=["重启后应用可自动或手动恢复连接",
                   "绑定关系保留，无需重新配对"],
         notes=""),
    dict(module="CONN", type="EXC", title="强射频干扰环境连接稳定性", priority="P2",
         preconditions="可制造干扰源（多个 BLE 设备/微波环境）",
         data="",
         steps=["干扰环境下发起连接并传输数据"],
         expected=["连接成功率不低于定义阈值，或按协议重试",
                   "数据传输丢包在可接受范围并有重传机制"],
         notes=""),
    # ---- Concurrency (CON) -------------------------------------------------
    dict(module="MULTI", type="CON", title="多设备同时发起连接（竞态）", priority="P1",
         preconditions="≥2 台未配对设备同时可发现",
         data="",
         steps=["两台设备同时向手机发起连接请求"],
         expected=["系统按策略处理（顺序连接/拒绝其一），不崩溃",
                   "最终状态与产品定义一致且可预期"],
         notes=""),
    dict(module="CONN", type="CON", title="频繁连接-断开循环稳定性", priority="P1",
         preconditions="设备已配对",
         data="循环次数=50",
         steps=["连续执行 连接→断开 循环 50 次"],
         expected=["循环过程中无崩溃、无假死",
                   "连接成功率≥95%，失败可恢复"],
         notes="压测类"),
    dict(module="CONN", type="CON", title="连接建立过程中触发断开", priority="P2",
         preconditions="连接建立中",
         data="",
         steps=["发起连接后立即触发断开操作"],
         expected=["断开操作生效，无状态残留",
                   "后续可正常重新连接"],
         notes=""),
    # ---- Security (SEC) -----------------------------------------------------
    dict(module="PAIR", type="SEC", title="Numeric Comparison 防中间人（MITM）确认", priority="P0",
         preconditions="双方均支持 Secure Connections",
         data="",
         steps=["发起配对，观察是否要求双方确认 6 位数字",
                "拒绝确认时观察配对结果"],
         expected=["未经双方确认无法完成配对",
                   "拒绝确认后配对失败，不建立不安全连接"],
         notes="安全合规"),
    dict(module="DATA", type="SEC", title="数据传输加密", priority="P0",
         preconditions="设备已连接，LE Secure Connections 已启用",
         data="",
         steps=["连接后抓取空中数据包，确认链路加密",
                "传输敏感数据"],
         expected=["链路层加密生效，明文数据不可直接读取",
                   "敏感数据传输正常无泄漏"],
         notes="安全合规"),
    dict(module="RECON", type="SEC", title="隐私地址（RPA）更新后重连", priority="P1",
         preconditions="设备开启隐私模式，已绑定",
         data="",
         steps=["绑定后等待设备地址周期更新",
                "地址更新后发起重连"],
         expected=["重连成功（依赖绑定密钥识别，而非固定地址）",
                   "未绑定的新地址设备无法冒充连接"],
         notes=""),
    dict(module="CONN", type="SEC", title="未授权设备连接被拒绝", priority="P1",
         preconditions="目标设备已与主机绑定",
         data="",
         steps=["使用另一台未绑定的主机尝试连接目标设备"],
         expected=["连接被拒绝或需重新配对，绑定关系不被覆盖"],
         notes=""),
    # ---- Performance (PERF) --------------------------------------------------
    dict(module="CONN", type="PERF", title="连接建立时延", priority="P1",
         preconditions="设备已配对",
         data="采样次数=10",
         steps=["冷启动连接 10 次，记录每次连接建立耗时",
                "统计平均/最大时延"],
         expected=["平均连接时延符合性能指标（如 <2s）",
                   "无单次异常超时"],
         notes=""),
    dict(module="DATA", type="PERF", title="数据传输吞吐", priority="P1",
         preconditions="设备已连接",
         data="传输总量=100MB",
         steps=["连续传输 100MB 数据，记录吞吐与时延分布"],
         expected=["吞吐达到定义指标（如 ≥100KB/s）",
                   "无连续丢包，重传率可控"],
         notes=""),
    dict(module="CONN", type="PERF", title="长时间稳定运行", priority="P1",
         preconditions="设备已连接并持续交互",
         data="时长=72 小时",
         steps=["持续连接并周期性传输数据 72 小时"],
         expected=["期间无意外掉线（允许计划内重连）",
                   "无内存泄漏、无崩溃，状态可恢复"],
         notes=""),
    dict(module="CONN", type="PERF", title="连接功耗影响", priority="P2",
         preconditions="可监测主机/设备电量",
         data="",
         steps=["对比蓝牙关闭与连接状态下的耗电增量"],
         expected=["连接状态耗电增量符合产品指标，无异常高耗电"],
         notes=""),
    # ---- Compatibility (COMPAT) ----------------------------------------------
    dict(module="CONN", type="COMPAT", title="Android/iOS 平台连接兼容", priority="P1",
         preconditions="Android 与 iOS 主机各一台，设备已分别配对",
         data="",
         steps=["分别在 Android 与 iOS 上执行 扫描-配对-连接-传输 全流程"],
         expected=["两平台全流程均正常，行为一致"],
         notes=""),
    dict(module="CONN", type="COMPAT", title="新旧系统版本兼容", priority="P2",
         preconditions="覆盖最新版与 3 个历史大版本",
         data="",
         steps=["在不同系统版本上执行核心连接流程"],
         expected=["核心流程在各版本均通过，无系统差异导致的功能缺失"],
         notes=""),
    dict(module="CONN", type="COMPAT", title="不同芯片方案兼容", priority="P2",
         preconditions="覆盖 2 种以上芯片方案（如 Nordic/TI）",
         data="",
         steps=["对每种芯片方案的样机执行 配对-连接-传输 流程"],
         expected=["各方案均能完成全流程，无芯片相关缺陷"],
         notes=""),
    # ---- Experience (EXP) ------------------------------------------------------
    dict(module="CONN", type="EXP", title="连接状态 UI 反馈", priority="P1",
         preconditions="设备已配对",
         data="",
         steps=["依次经历 扫描中→连接中→已连接→已断开 各状态，观察 UI"],
         expected=["每个状态都有明确 UI 反馈（图标/文案/动画）",
                   "状态切换无闪烁、无错误显示"],
         notes=""),
    dict(module="CONN", type="EXP", title="失败提示文案可理解", priority="P2",
         preconditions="可制造连接失败场景",
         data="",
         steps=["触发连接失败（超时/权限拒绝/对端忙）"],
         expected=["提示文案准确描述失败原因并给出可执行建议",
                   "无技术术语堆砌、无空白错误"],
         notes=""),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

MODULE_NAMES = {
    "SCAN": "扫描/发现", "PAIR": "配对/绑定", "CONN": "连接", "DISC": "断开",
    "RECON": "重连", "DATA": "数据传输", "MULTI": "多连接", "SEC": "安全",
    "PERF": "性能", "COMPAT": "兼容",
}
TYPE_NAMES = {
    "FUN": "功能", "BND": "边界", "EXC": "异常", "CON": "并发",
    "SEC": "安全", "PERF": "性能", "COMPAT": "兼容", "EXP": "体验",
}


def fmt_steps(steps):
    return "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))


def fmt_expected(expected):
    return "\n".join(f"{i}. {s}" for i, s in enumerate(expected, 1))


def build_case(seq, sc, product):
    case_id = f"TC-{sc['module']}-{sc['type']}-{seq:03d}"
    return {
        "用例ID": case_id,
        "标题": f"[{product}] {sc['title']}",
        "优先级": sc["priority"],
        "测试类型": TYPE_NAMES.get(sc["type"], sc["type"]),
        "模块": MODULE_NAMES.get(sc["module"], sc["module"]),
        "前置条件": sc["preconditions"],
        "测试数据": sc["data"],
        "测试步骤": fmt_steps(sc["steps"]),
        "预期结果": fmt_expected(sc["expected"]),
        "备注": sc["notes"],
    }


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows, product, platform, bt_type, path):
    total = len(rows)
    prio = Counter(r["优先级"] for r in rows)
    types = Counter(r["测试类型"] for r in rows)
    modules = Counter(r["模块"] for r in rows)
    lines = [
        f"# 蓝牙连接测试用例 - {product}",
        "",
        f"- 平台：{platform} ｜ 蓝牙类型：{bt_type} ｜ 用例总数：{total}",
        f"- 优先级分布：P0={prio.get('P0', 0)}，P1={prio.get('P1', 0)}，P2={prio.get('P2', 0)}，P3={prio.get('P3', 0)}",
        f"- 测试类型：{', '.join(f'{k}={v}' for k, v in types.items())}",
        "",
        "## 按模块分布",
        "",
        "| 模块 | 用例数 |",
        "|---|---|",
    ]
    for m, c in sorted(modules.items(), key=lambda x: -x[1]):
        lines.append(f"| {m} | {c} |")
    lines += ["", "## 用例明细", ""]
    current_module = None
    for r in rows:
        if r["模块"] != current_module:
            current_module = r["模块"]
            lines += ["", f"### {current_module}", ""]
        lines += [
            f"**{r['用例ID']}** · {r['标题']} · **{r['优先级']}** · {r['测试类型']}",
            "",
            f"- 前置条件：{r['前置条件']}",
            f"- 测试数据：{r['测试数据'] or '—'}",
            "",
            "测试步骤：",
            r["测试步骤"].replace("\n", "\n"),
            "",
            "预期结果：",
            r["预期结果"].replace("\n", "\n"),
            "",
            f"- 备注：{r['备注'] or '—'}",
            "",
        ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate enterprise Bluetooth connectivity test cases")
    parser.add_argument("--product", default="未命名产品", help="被测产品名称")
    parser.add_argument("--platform", default="android", choices=["android", "ios", "pc", "embedded"],
                        help="被测主机平台")
    parser.add_argument("--bt-type", default="ble", choices=["ble", "br-edr", "dual"],
                        help="蓝牙类型")
    parser.add_argument("--modules", default="SCAN,PAIR,CONN,DISC,RECON,DATA,MULTI,SEC,PERF,COMPAT",
                        help="逗号分隔的模块码列表")
    parser.add_argument("--dimensions", default="FUN,BND,EXC,CON,SEC,PERF,COMPAT,EXP",
                        help="逗号分隔的测试类型码列表")
    parser.add_argument("--min-priority", default="P3", choices=["P0", "P1", "P2", "P3"],
                        help="最低包含的优先级（P0 只出 P0，P3 出全部）")
    parser.add_argument("--out", default="test_cases.csv", help="CSV 输出路径")
    parser.add_argument("--report", default="test_cases.md", help="Markdown 报告输出路径")
    args = parser.parse_args(argv)

    modules = {m.strip().upper() for m in args.modules.split(",") if m.strip()}
    dimensions = {d.strip().upper() for d in args.dimensions.split(",") if d.strip()}
    min_prio = PRIORITY_ORDER[args.min_priority]

    selected = [
        sc for sc in SCENARIOS
        if sc["module"] in modules
        and sc["type"] in dimensions
        and PRIORITY_ORDER[sc["priority"]] <= min_prio
    ]
    if not selected:
        print("ERROR: no scenarios match the given modules/dimensions/priority.", file=sys.stderr)
        sys.exit(2)

    # Deterministic ordering: by module, then type, then priority, then original order.
    selected.sort(key=lambda sc: (MODULE_NAMES.get(sc["module"], sc["module"]),
                                  TYPE_NAMES.get(sc["type"], sc["type"]),
                                  PRIORITY_ORDER[sc["priority"]],
                                  SCENARIOS.index(sc)))
    rows = [build_case(i + 1, sc, args.product) for i, sc in enumerate(selected)]

    write_csv(rows, args.out)
    write_markdown(rows, args.product, args.platform, args.bt_type, args.report)

    prio = Counter(r["优先级"] for r in rows)
    print(f"OK: generated {len(rows)} test cases -> {args.out}, {args.report}")
    print(f"    priority: {dict(prio)}")


if __name__ == "__main__":
    main()
