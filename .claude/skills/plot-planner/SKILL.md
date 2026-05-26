---
name: plot-planner
description: >
  从故事构思出发，规划卷/篇章结构，拆解为逐章剧情指令。
  支持纯文本、JSON、Markdown 格式大纲，自动注入硬性写作约束。
  触发词：剧情规划、大纲设计、拆解大纲、章节分解、写作指令、逐章prompt
  前置需求：world_settings.md, characters.md（可选但有会更好）
---

# Plot Planner — 剧情规划

## 工作流

### 第 1 步：定义故事主干

如果用户没有现成大纲，帮用户定义：

1. **一句话梗概**：谁 + 在什么世界 + 要做什么 + 面临什么阻碍
2. **主线冲突**：核心矛盾是什么？
3. **类型定位**：玄幻/都市/科幻/历史/言情/悬疑？
4. **目标篇幅**：多少卷？多少章？

### 第 2 步：设计卷/篇章结构

将故事拆分为 3-8 卷/篇章，每卷定义：
- 卷名 + 主题
- 起止章节范围
- 本卷核心冲突
- 角色在本卷中的状态变化
- 高潮事件

参考 `shared/templates/plot_outline.md` 的情节节点表。

### 第 3 步：逐章拆解

把每卷拆解成章节列表，每章定义：
- 章号 + 章节标题
- POV 角色
- 本章情节（100-300 字描述）
- 目标字数（默认 8,000-12,000 字）
- 本章钩子类型（悬念/反转/新信息/情感冲击）
- 本章出场的核心角色

### 第 4 步：生成写作指令

运行解析脚本生成逐章写作指令：

```bash
python .claude/skills/plot-planner/scripts/parse_outline.py \
  --outline plot_outline.md \
  --output chapters/briefs/
```

可选的上下文文件（提升指令质量）：
```bash
python .claude/skills/plot-planner/scripts/parse_outline.py \
  --outline plot_outline.md \
  --output chapters/briefs/ \
  --context .storyai/context.json
```

上下文 JSON 格式：
```json
{
  "world_summary": "世界观摘要（500字内）",
  "character_context": "核心角色摘要（每角色100字）"
}
```

### 第 5 步：情感曲线覆叠

在逐章拆解完成后，覆叠情感强度曲线：
- 标记每章的情感强度（1-10）
- 确保高潮和低谷交替，不是所有章都是 8+
- 识别节奏问题（连续 5 章高强度或连续 5 章低强度 → 调整）

## 输出文件

- `plot_outline.md` — 完整大纲文档
- `chapters/briefs/NNNN.md` — 每章写作指令
- `chapters/briefs/chapter_briefs.json` — 章节摘要 JSON

## 约束

- 每个写作指令自动注入硬性约束：纯中文、零 AI 标记词、字数目标、禁止模板化结尾
- 如果提供了世界观和角色上下文，注入相关摘要
- 情感曲线的节奏必须合理
