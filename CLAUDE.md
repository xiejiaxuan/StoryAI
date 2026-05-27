# CLAUDE.md

## Project Overview

StoryAI 是一个基于 Claude Code Skill 体系的 AI 长篇小说写作助手系统。8 个模块化 Skill 覆盖从世界观构建到整本输出的完整写作流水线。

**核心定位**：纯 Claude Code 原生，无需外部服务器、数据库或 LLM API。所有创意生成由 Claude 完成，辅助脚本使用 Python 3 标准库。

## Directory Structure

```
StoryAI/
├── CLAUDE.md                          # 本文件
├── .claude/skills/                    # 8 个 Claude Code Skill
│   ├── pipeline-orchestrator/         # 全流程编排
│   ├── world-builder/                 # 世界观构建
│   ├── character-designer/            # 角色设计
│   ├── plot-planner/                  # 剧情规划
│   ├── chapter-writer/                # 章节写作
│   ├── quality-checker/               # 质量控制
│   ├── ai-humanizer/                  # 去 AI 味
│   └── consistency-tracker/           # 一致性追踪
├── shared/
│   ├── rules/                         # 通用写作规则（适用于所有小说）
│   ├── scripts/                       # 共享 Python 工具（纯 stdlib）
│   ├── templates/                     # 输出结构模板
│   └── references/                    # 参考标准文档
└── novels/
    └── 曼巴重生/                       # 每本小说独立目录
        ├── chapters/                   # 章节正文
        ├── .storyai/                   # 本小说运行时状态 + 特定规则
        ├── world_settings.md
        ├── characters.md
        └── plot_outline.md
```
**多小说支持**：`shared/` 是通用层，每本小说在 `novels/<书名>/` 下拥有独立的一切（章节、设定、规则、状态）。

## How to Use

### 方式一：全流程编排

```
"我要写一本小说" / "开始写小说" / "从零开始写一本玄幻小说"
```

自动触发 `pipeline-orchestrator`，引导完成：项目设置 → 世界观 → 角色 → 大纲 → 逐章写作循环。

### 方式二：独立调用 Skill

| 你说的话 | 触发的 Skill |
|---------|-------------|
| "构建世界观" / "世界观设定" | world-builder |
| "设计角色" / "人物设定" | character-designer |
| "规划大纲" / "拆解大纲" | plot-planner |
| "写第5章" / "续写下一章" | chapter-writer |
| "审核第5章" / "看看质量" | quality-checker |
| "去AI味" / "太AI了改一下" | ai-humanizer |
| "检查一致性" / "有没有矛盾" | consistency-tracker |

## Skill Pipeline

```
构思 → 世界观 → 角色 → 大纲→逐章写作指令
                                    ↓
                   逐章循环: [写 → 审 → 去AI味 → 一致性检查 → 审批]
                                    ↓
                              整本编译输出
```

## File Naming Conventions

每本小说在 `novels/<书名>/` 下有独立的文件。当前工作目录应切换到小说目录下。

- 世界观：`world_settings.md`
- 角色档案：`characters.md`
- 剧情大纲：`plot_outline.md`
- 写作指令：`chapters/briefs/NNNN.md` + `chapter_briefs.json`
- 章节正文：`chapters/chapter_NNNN.md`
- 去 AI 味后：`chapters/chapter_NNNN_humanized.md`
- 审核报告：`reports/chapter_NNNN_quality.md`
- 实体数据库：`.storyai/entity_db.json`
- 一致性报告：`consistency_report.md`
- 流水线状态：`.storyai/state.json`
- 小说特定规则：`.storyai/novel-rules.md`

## Scripts

所有脚本使用 Python 3.8+ stdlib，零 pip 依赖。脚本做确定性计算（字数统计、正则匹配、JSON 解析），Claude 做创意生成和判断。

关键脚本：
- `quality_check.py` — 33 维度质量审核引擎
- `detect_patterns.py` — 51 条 AI 腔模式扫描器
- `parse_outline.py` — 大纲到逐章写作指令的转换器
- `ai_detector_quick.py` — AI 标记词快速检测（Top-20）
- `extract_entities.py` — 章节实体信息提取
- `validate_structure.py` — 世界观文档完整性验证

## Language Conventions

- 所有小说输出为**简体中文**
- 代码注释和变量名可以使用英文
- 文档和模板使用中文
- 章节格式：纯中文，数字用中文写法（一、二、三十），无阿拉伯数字，无英文

## Quality Standards

- **AI 标记词零容忍**：51 条 AI 腔模式（详见 `shared/references/ai_patterns.md`）
- **5 层 33 维度审核**：基础指标 → 文风结构 → 内容大纲 → 格式规范 → 高级分析
- **一致性保证**：跨章实体追踪，防止时空/规则/角色矛盾
- **去 AI 味双层机制**：写作时约束注入（预防）+ 写后扫除打磨（治疗）
