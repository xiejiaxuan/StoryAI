---
name: pipeline-orchestrator
description: >
  StoryAI 全流程编排器。引导用户从一句构思走到完整小说——
  世界观 → 角色 → 大纲 → 逐章写作+审核+去AI味+一致性检查 → 整本编译。
  也可以单独调用任何子 skill。
  触发词：开始写小说、从零开始、创建新项目、开始写作流程、我需要写一本
---

# Pipeline Orchestrator — 全流程编排

## 项目初始化

当用户表示要开始写小说时，首先创建项目结构：

1. 创建 `.storyai/` 目录和 `config.json`
2. 向用户确认：
   - **书名**
   - **类型**（玄幻/都市/科幻/历史/言情/悬疑/其他）
   - **目标篇幅**（卷数 + 章数范围）
   - **POV 风格**（第三人称有限视角 推荐）
   - **调性**（轻松/严肃/黑暗/热血/幽默）

config.json 格式：
```json
{
  "format_version": "1.0",
  "title": "书名",
  "genre": "玄幻",
  "target_chapters": 50,
  "pov_style": "third_person_limited",
  "tone": "serious",
  "created_at": "2026-05-26T00:00:00Z"
}
```

## 流水线阶段

### 阶段 0：项目初始化 ✓

### 阶段 1：世界构建
- 调用 world-builder skill
- 等待用户审批 world_settings.md
- 批准 → 进入阶段 2
- 驳回 → 根据用户反馈迭代

### 阶段 2：角色设计
- 调用 character-designer skill
- 等待用户审批 characters.md
- 批准 → 进入阶段 3
- 驳回 → 根据用户反馈迭代

### 阶段 3：剧情规划
- 调用 plot-planner skill
- 生成卷/篇章结构 + 逐章写作指令
- 等待用户审批 plot_outline.md + chapter_briefs.json
- 用户确认情感曲线合理
- 批准 → 进入阶段 4

### 阶段 4：逐章生产（循环）
对每一章执行：

```
4a. 写作
    → 调用 chapter-writer 写当前章
    → 输出 chapters/chapter_NNNN.md

4b. 质量审核
    → 调用 quality-checker 审核本章
    → 输出 reports/chapter_NNNN_quality.md
    → 如果有关键问题 → 返回 4a 修订

4c. 去 AI 味
    → 调用 ai-humanizer 处理本章
    → 输出 chapters/chapter_NNNN_humanized.md

4d. 一致性检查
    → 调用 consistency-tracker 更新实体库
    → 输出 consistency_report.md（增量更新）
    → 如果有矛盾 → 提醒用户

4e. 用户审批
    → 展示：章节 + 审核报告 + 一致性警告
    → 用户选择：批准 / 修订 / 跳过
    → 批准或跳过 → 进入下一章
    → 修订 → 返回 4a（指定修订要求）
```

### 阶段 5：整本编译
- 合并所有 humanized 章节
- 运行全局一致性检查
- 生成目录
- 输出完整稿件

## 状态追踪

state.json 跟踪所有进度：
```json
{
  "phase": "production",
  "current_chapter": 5,
  "total_chapters_planned": 50,
  "chapter_status": {
    "1": "complete",
    "2": "complete",
    "3": "review",
    "5": "writing"
  }
}
```

流水线可以随时中断和恢复——读取 state.json 就知道该从哪里继续。

## 独立调用

用户也可以单独调用任何 skill，不经过编排器：
- "构建世界观" → world-builder
- "设计角色" → character-designer
- "规划大纲" → plot-planner
- "写第 5 章" → chapter-writer
- "审核第 5 章" → quality-checker
- "给第 5 章去 AI 味" → ai-humanizer
- "检查一致性" → consistency-tracker
