# 热点挖掘工具链

> 每日自动采集微博/知乎/B站/百度/抖音热搜 → AI 分析小说潜力 → 输出可用素材

## 架构

```
┌──────────────────────────────────────────────────┐
│                  热点挖掘工具链                      │
├──────────────────────────────────────────────────┤
│                                                    │
│  [定时触发]  cron: 每天 9:00 + 21:00               │
│       │                                            │
│       ▼                                            │
│  [数据采集]  collect_hotspots.py                   │
│       │  微博 · 知乎 · B站 · 百度 · 抖音 · 头条      │
│       │  输出: data/hotspots_YYYYMMDD_HHMMSS.json  │
│       │        data/latest.json (最新一份)          │
│       ▼                                            │
│  [AI 分析]  Hermes Agent + hotspot-novel-miner     │
│       │  评分(冲突性/延展性/共鸣度/差异化)           │
│       │  分级(A/B/C/D)                              │
│       │  生成小说开篇方案                            │
│       ▼                                            │
│  [素材输出]  output/novel_materials_YYYYMMDD.json   │
│       │                                            │
│       ▼                                            │
│  [人工筛选]  你决定用哪个方案 →                     │
│       │                                            │
│       ▼                                            │
│  [StoryAI]  F:\StoryAI\novels\<书名>\              │
│       → xianxia-novel-workshop Stage 1             │
│                                                    │
└──────────────────────────────────────────────────┘
```

## 文件说明

```
hotspot-tools/
├── README.md                     # 本文件
├── collect_hotspots.py           # 多源热搜采集器
├── data/
│   ├── hotspots_YYYYMMDD_HHMMSS.json  # 历史采集数据
│   └── latest.json                    # 最新一份（AI 分析的输入）
└── output/
    └── novel_materials_YYYYMMDD.json  # AI 分析输出（小说素材）
```

## 使用方法

### 手动运行

```bash
# 采集所有平台热搜
cd F:\StoryAI\hotspot-tools
python collect_hotspots.py

# 只采集微博
python collect_hotspots.py --source weibo

# 只采集抖音
python collect_hotspots.py --source douyin
```

然后对我说：
> "运行 hotspot-novel-miner 分析最新热点"

### 自动运行

已设置 cron 定时任务：**每天 9:00 和 21:00 自动采集+分析**

查询状态：
> "查看 cron 任务"

## 数据源覆盖

| 平台 | 方法 | 稳定性 |
|------|------|--------|
| 微博热搜 | 半公开 API | ★★★★★ |
| 知乎热榜 | API + RSS 降级 | ★★★ |
| B站热门 | 公开 API | ★★★★★ |
| 百度热搜 | HTML 解析 + JSON | ★★★★ |
| 抖音热点 | 第三方聚合代理 | ★★★ |
| 今日头条 | 第三方聚合代理 | ★★★ |

## AI 分析维度

| 维度 | 权重 | 评估内容 |
|------|------|---------|
| 冲突性 | 30% | 是否有内在冲突？道德困境？人vs命运？ |
| 延展性 | 25% | 能否支撑50章+？有世界观扩展空间？ |
| 共鸣度 | 25% | 读者会情感共鸣吗？触及普遍恐惧/欲望？ |
| 差异化 | 20% | 新鲜角度还是烂梗？有让人点击的钩子吗？ |

≥7.0 = 强小说潜力

## 分级标准

- **A级**: 可直接作为小说开篇
- **B级**: 核心冲突好，需类型改编
- **C级**: 单个元素可吸收进现有小说
- **D级**: 不适合（纯娱乐/体育比分/明星八卦）
