"""
每日数据记录工具
=================
用于手动记录平台后台数据到 metrics_log.json
不需要输入任何参数，交互式问答。

运行: python log_metrics.py
"""

import json, os
from datetime import datetime, timezone, timedelta

BEIJING_TZ = timezone(timedelta(hours=8))
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics_log.json")

# 如果有已有日志，加载；否则创建新的
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log = json.load(f)
else:
    log = {
        "novel": "",
        "platform": "",
        "first_publish_date": "",
        "records": []
    }

# 首次使用时填写基本信息
if not log.get("novel"):
    log["novel"] = input("小说名: ").strip()
if not log.get("platform"):
    log["platform"] = input("发布平台(番茄小说/起点/七猫/晋江): ").strip()
if not log.get("first_publish_date"):
    log["first_publish_date"] = input("首发日期(YYYY-MM-DD): ").strip()

print(f"\n  小说: {log['novel']} | 平台: {log['platform']}")
print(f"  已记录 {len(log.get('records', []))} 天\n")

# 本日记录
today = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")

# 检查今天是否已经记录过
existing = [r for r in log.get("records", []) if r.get("date") == today]
if existing:
    print(f"  ⚠️ 今天({today})已记录过。覆盖? (y/n): ", end="")
    if input().strip().lower() != "y":
        print("  已取消")
        exit(0)

record = {"date": today}

print("=== 小说信息 ===")
record["total_chapters_published"] = int(input("已发布章节数: ").strip() or "0")
record["total_words"] = int(input("累计字数: ").strip() or "0")

print("\n=== 阅读数据 ===")
record["metrics"] = {}
m = record["metrics"]
m["累计阅读"] = int(input("累计阅读量: ").strip() or "0")
m["追读人数"] = int(input("追读人数: ").strip() or "0")
m["昨日新增阅读"] = int(input("昨日新增阅读: ").strip() or "0")
m["读完率"] = float(input("当前读完率(0-1): ").strip() or "0")

print("\n=== 收益数据 ===")
m["昨日收益"] = float(input("昨日收益(元): ").strip() or "0")
m["累计收益"] = float(input("累计收益(元): ").strip() or "0")

print("\n=== 互动数据 ===")
m["评论数"] = int(input("评论数: ").strip() or "0")
m["书架数"] = int(input("加入书架数: ").strip() or "0")
score = input("评分(直接回车跳过): ").strip()
if score:
    m["评分"] = float(score)

print("\n=== 备注 ===")
notes = input("备注(上了什么推荐/做了什么事): ").strip()
if notes:
    record["notes"] = notes

# 如果今天已有记录，替换；否则追加
if existing:
    idx = log["records"].index(existing[0])
    log["records"][idx] = record
else:
    log["records"].append(record)

# 保存
with open(LOG_FILE, "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)

print(f"\n  ✅ 已保存 ({today})")
print(f"  📊 累计阅读: {m['累计阅读']} | 追读: {m['追读人数']} | 收益: ¥{m['累计收益']}")

# 自动提醒
if log["records"]:
    recent = log["records"][-7:] if len(log["records"]) >= 7 else log["records"]
    if len(recent) >= 3:
        avg_new_reads = sum(r["metrics"]["昨日新增阅读"] for r in recent) / len(recent)
        if avg_new_reads < 50 and record["total_chapters_published"] >= 40:
            print(f"\n  ⚠️ 近{len(recent)}天平均新增阅读 {avg_new_reads:.0f}，建议关注读完率并考虑加速收尾")
