# 仙侠小说创作完整工作流

> 本文件是操作手册——按顺序执行即可。

---

## 架构总览

```
工作流 = 研究层 + 技能层 + 流水线层

研究层（已完成）
  └── F:\StoryAI\zhu-xian-study\  ← 11 份研究文档

技能层（已创建）
  └── Hermes Skill: xianxia-novel-workshop  ← 6 阶段流水线

流水线层（待执行）
  └── F:\StoryAI\novels\未命名仙侠\  ← 你的小说目录
```

---

## 快速开始：现在就可以做的事

### 第一步：确定核心理念（5 分钟）

打开 `F:\StoryAI\zhu-xian-study\synthesis.md`，跳到第六节，从候选核心理念中挑一个（或自己定义）：

| 核心理念 | 适合的故事方向 |
|----------|-------------|
| "何为仙？何为魔？" | 正邪灰度、身份认同危机 |
| "凡人能否逆天？" | 命运对抗、力量代价 |
| "长生何用？" | 修炼终极意义的追问 |
| "力量与人性能否共存？" | 修炼对人性的侵蚀 |

### 第二步：启动第一阶段（30 分钟）

对我说：
> "按照 xianxia-novel-workshop 技能，开始 Stage 1：世界观构建和战力体系设计"

我会带你一步步完成：
- 地理/势力分布
- 修炼境界体系（3大阶9小层）
- 多路径修炼设计
- 核心法宝设计
- 终极力量的代价

输出：`world_settings.md`

### 第三步：启动第二阶段（30 分钟）

> "开始 Stage 2：角色设计"

输出：`characters.md`

### 第四步：启动第三阶段（45 分钟）

> "开始 Stage 3：剧情规划"

输出：`plot_outline.md`

### 第五步：拷打大纲（15 分钟）

> "开始 Stage 4：拷打大纲"

我会逐项检查因果链、角色动机、感情线功能、战力一致性。

### 第六步：开始写第一章

> "开始 Stage 5：写第一章"

进入逐章生产循环。

---

## 两种使用方式

### 方式 A：全自动（推荐）

直接对我说：
> "按照 xianxia-novel-workshop 技能，从 Stage 0 开始，帮我完成仙侠小说项目初始化"

我会按顺序带你走完全流程，每步等你审批。

### 方式 B：分步调用

随时对我说：
> "运行 Stage 1" / "设计角色" / "规划大纲" / "写第 N 章" / "拷打第 N 章"

---

## 文件结构速查

```
F:\StoryAI\
├── zhu-xian-study\              ← 诛仙研究（已完成）
│   ├── README.md
│   ├── synthesis.md              ← ★ 创作方法论总结
│   ├── world-building/           ← 世界观 + 战力体系
│   ├── characters/               ← 角色分析 + 关系图谱
│   ├── plot-structure/           ← 结构拆解 + 推进手法
│   ├── style-analysis/           ← 文笔 + 节奏分析
│   └── romance-arcs/             ← 感情线分析
│
├── novels\未命名仙侠\            ← 你的小说（待填充）
│   ├── .storyai\
│   │   ├── config.json           ← 小说元数据 ✓
│   │   ├── state.json            ← 进度追踪 ✓
│   │   └── novel-rules.md        ← 本小说规则 ✓
│   ├── world_settings.md         ← Stage 1 产出
│   ├── characters.md             ← Stage 2 产出
│   ├── plot_outline.md           ← Stage 3 产出
│   ├── chapters/                 ← 章节正文
│   └── reports/                  ← 审核报告
│
└── .claude\skills\               ← 原有的 9 个 Claude Code 技能
    ├── pipeline-orchestrator/
    ├── world-builder/
    ├── character-designer/
    ├── plot-planner/
    ├── chapter-writer/
    ├── quality-checker/
    ├── ai-humanizer/
    ├── consistency-tracker/
    └── grill-with-docs/
```

---

## 关键规则文件

写每一章之前，必须回顾这些规则文件：

| 文件 | 内容 | 重要程度 |
|------|------|---------|
| `novel-rules.md` | 本小说的特定约束 | ★★★★★ |
| `shared/rules/chinese-novel-writing.md` | 通用中文小说规则 | ★★★★★ |
| `shared/references/ai_patterns.md` | 51 条 AI 腔禁止模式 | ★★★★ |
| `shared/references/deai_rules.md` | 10 条去 AI 化规则 | ★★★★ |
| `zhu-xian-study/style-analysis/writing-style.md` | 诛仙式文风参考 | ★★★ |

---

## 常见问题

### Q: 我应该从哪一步开始？
A: 从 Stage 0 开始——先定书名和核心理念。其他都取决于这个。

### Q: 我需要一口气完成所有 Stage 吗？
A: 不需要。每个 Stage 完成后会保存状态到 state.json，随时中断随时继续。

### Q: 研究文档需要全部读完吗？
A: 不需要。每个 Stage 会告诉你具体读哪几份研究文档。synthesis.md 是核心总结，最值得先读。

### Q: 和原有的 Claude Code 技能冲突吗？
A: 不冲突。Hermes Skill 负责流程编排，底层仍可调用 Claude Code 的 world-builder / character-designer 等技能来生成具体内容。两者互补。
