# OpenSpace Claude Evolution

OpenSpace Claude Evolution 是由**关镇江**基于香港大学 Data Intelligence Lab 开源项目 [OpenSpace](https://github.com/HKUDS/OpenSpace) 改造的私有化演化平台。

本项目保留 OpenSpace 原生的 `SKILL.md` 自我进化能力，同时新增对 `.claude` 团队共享系统的兼容能力，用于演化：

- `.claude/commands/*.md`
- `.claude/templates/*.md`
- `.claude/reference/*.md`
- `CLAUDE.md / PRD.md / prime-context.md / validation-context.md`

本项目遵循 MIT License，并保留原始来源说明。  
源码来源：香港大学开源项目 OpenSpace。  
当前仓库改造与维护：关镇江。

## 项目目标

本项目解决两类问题：

1. 保留 OpenSpace 原生的技能演化能力
- `FIX`
- `DERIVED`
- `CAPTURED`

2. 增加 `.claude` 团队共享系统的专用演化能力
- 识别命令、模板、知识卡片、正式记忆的漂移
- 所有演化结果先落草稿
- 草稿统一输出到 `.claude/evolution-drafts/`
- 不直接覆盖正式 `.claude` 文件

## 当前改造原则

本仓库严格遵循以下设计：

- `OpenSpace兼容.claude团队共享系统的Artifact进化模型设计`
- `OpenSpace原生Skill与.claude Artifact的DEPRECATE机制设计`
- `OpenSpace与.claude的模型能力增强退役硬标准`

核心约束：

- 不破坏 OpenSpace 原生 `SKILL.md` 管线
- `.claude` 兼容能力以旁路扩展方式实现
- 云社区默认禁用
- 自动演化结果先出草稿，不直接改正式规则

## 与原始 OpenSpace 的主要区别

### 1. 云社区默认禁用

本仓库默认关闭云社区相关能力：

- 默认不上传公共社区
- 默认不下载公共社区
- 默认只支持本地或公司内使用

如需重新启用，必须显式设置：

```bash
OPENSPACE_DISABLE_CLOUD_COMMUNITY=false
```

### 2. 新增 `.claude` Artifact 识别

当工作区包含 `.claude/` 时，系统会识别并分类：

- `command_alias`
- `command_workflow`
- `claude_template`
- `claude_memory`
- `reference_card`
- `reference_index`
- `reference_feedback`
- `reference_template`

### 3. 新增 `.claude/evolution-drafts/`

所有 `.claude` 侧自动演化结果统一先落到：

```text
.claude/evolution-drafts/
```

默认子目录：

- `commands/`
- `templates/`
- `reference/`
- `memory/`
- `reports/`

### 4. 预留 `DEPRECATE` 生命周期

本项目为后续两条线预留了生命周期治理：

- OpenSpace 原生 skill 的软退役
- `.claude` Artifact 的软退役

退役机制不是自动删除，而是：

```text
候选 -> 软降权 -> deprecated -> 人工归档/删除
```

## 安装与启动

## 环境要求

- Python 3.12+
- Git
- 支持 MCP 的宿主 Agent
- Windows / macOS / Linux

## Windows 本机安装

如果你在 Windows 上直接使用，推荐按下面的顺序执行：

```powershell
git clone https://github.com/UF-gzj/openspace-claude-evolution.git
cd openspace-claude-evolution
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m openspace.mcp_server --help
```

如果你已经有现成 Python 环境，也可以直接：

```powershell
git clone https://github.com/UF-gzj/openspace-claude-evolution.git
cd openspace-claude-evolution
python -m pip install -e .
python -m openspace.mcp_server --help
```

## 轻量克隆

如果你只想先拉代码再安装：

```bash
git clone --filter=blob:none --sparse https://github.com/UF-gzj/openspace-claude-evolution.git
cd openspace-claude-evolution
git sparse-checkout set "/*" "!assets/"
python -m pip install -e .
```

## 开发安装

如果要参与二次开发：

```bash
git clone https://github.com/UF-gzj/openspace-claude-evolution.git
cd openspace-claude-evolution
python -m pip install -e .[dev]
```

## 模型凭据来源

如果没有显式设置 `OPENSPACE_LLM_API_KEY` 和 `OPENSPACE_LLM_API_BASE`，OpenSpace 会按以下顺序继续尝试解析本地可用凭据：

1. provider-native 环境变量
2. nanobot 配置
3. openclaw 配置
4. 本机 Claude Code 配置 `~/.claude/settings.json`

这意味着在本机 Claude Code 已登录可用时，OpenSpace 可以直接复用其本地鉴权信息，无需再手动重复填写一套 `OPENSPACE_LLM_*`。

## 启动 MCP 服务

最稳的启动方式是：

```bash
python -m openspace.mcp_server
```

如果需要显式指定传输方式：

```bash
python -m openspace.mcp_server --transport stdio
python -m openspace.mcp_server --transport sse --port 8080
python -m openspace.mcp_server --transport streamable-http --port 8080
```

如果本机安装后的 `Scripts` 目录没有加入 `PATH`，优先使用 `python -m openspace.mcp_server`，不要依赖 `openspace-mcp` 命令名。

## 环境变量

最常用的环境变量：

```bash
OPENSPACE_MODEL=openrouter/anthropic/claude-sonnet-4.5
OPENSPACE_DISABLE_CLOUD_COMMUNITY=true
OPENSPACE_ENABLE_CLAUDE_EVOLUTION=false
OPENSPACE_ENABLE_CLAUDE_DEPRECATION=false
OPENSPACE_ENABLE_SKILL_DEPRECATION=false
OPENSPACE_WORKSPACE=/path/to/your/project
OPENSPACE_HOST_SKILL_DIRS=/path/to/host/skills
```

其中：

- `OPENSPACE_DISABLE_CLOUD_COMMUNITY=true`
  - 默认关闭云社区
- `OPENSPACE_ENABLE_CLAUDE_EVOLUTION=true`
  - 启用 `.claude` Artifact 兼容和草稿目录创建
- `OPENSPACE_ENABLE_CLAUDE_DEPRECATION=true`
  - 启用 `.claude` 侧生命周期治理
- `OPENSPACE_ENABLE_SKILL_DEPRECATION=true`
  - 启用原生 skill 软退役生命周期

建议最小环境变量组合：

```bash
OPENSPACE_DISABLE_CLOUD_COMMUNITY=true
OPENSPACE_WORKSPACE=D:/Desktop/cfs-report
OPENSPACE_ENABLE_CLAUDE_EVOLUTION=true
OPENSPACE_ENABLE_CLAUDE_DEPRECATION=true
OPENSPACE_ENABLE_SKILL_DEPRECATION=true
```

## 作为 MCP 接入

宿主侧 MCP 配置示例：

```json
{
  "mcpServers": {
    "openspace": {
      "command": "python",
      "args": ["-m", "openspace.mcp_server"],
      "toolTimeout": 600,
      "env": {
        "OPENSPACE_WORKSPACE": "D:/Desktop/cfs-report",
        "OPENSPACE_HOST_SKILL_DIRS": "D:/agent/skills",
        "OPENSPACE_DISABLE_CLOUD_COMMUNITY": "true",
        "OPENSPACE_ENABLE_CLAUDE_EVOLUTION": "true",
        "OPENSPACE_ENABLE_CLAUDE_DEPRECATION": "true",
        "OPENSPACE_ENABLE_SKILL_DEPRECATION": "true"
      }
    }
  }
}
```

## 常规使用流程

### 场景一：只使用原生 OpenSpace skill 能力

适合：

- 继续使用 `SKILL.md`
- 继续让 OpenSpace 处理 skill 检索、执行、修复、派生、捕获

流程：

1. 安装本项目
2. 配置 MCP
3. 配置宿主 skill 目录
4. 让 OpenSpace 正常接管原生 skill 工作流

### 原生 skill 常用能力

启用后，最常用的是这几类能力：

- `execute_task`
  - 执行真实任务，并自动尝试检索本地 skill
- `search_skills`
  - 搜索本地 skill 或云端 skill
- `fix_skill`
  - 修复已有 skill
- 自动演化
  - `FIX`
  - `DERIVED`
  - `CAPTURED`

原生 skill 仍是 OpenSpace 的第一主线，这部分不会因为 `.claude` 兼容而被替代。

### 场景二：启用 `.claude` 团队共享系统兼容

适合：

- 你的项目目录里已经有 `.claude/`
- 希望系统识别 `.claude` 命令、模板、reference、正式记忆
- 希望未来把演化结果统一输出到 `.claude/evolution-drafts/`

流程：

1. 项目目录必须包含 `.claude/`
2. 设置：

```bash
OPENSPACE_WORKSPACE=/path/to/project
OPENSPACE_ENABLE_CLAUDE_EVOLUTION=true
```

3. 启动 OpenSpace
4. 系统会检测当前 workspace 是否存在 `.claude/`
5. 如果存在，会自动准备：

```text
.claude/evolution-drafts/
```

同时会在工作区生成：

```text
.openspace/lifecycle/lifecycle.json
```

用于记录 `.claude` artifact 与原生 skill 的生命周期治理状态，但不会直接覆盖正式 `.claude` 文件。

如需显式生成 `.claude` 评估草稿，可通过 MCP 调用：

```text
analyze_claude_artifacts(write_drafts=true)
```

草稿会写入：

```text
.claude/evolution-drafts/commands/
.claude/evolution-drafts/templates/
.claude/evolution-drafts/reference/
.claude/evolution-drafts/memory/
```

如需在评估基础上进一步生成可审阅的修复提案，可调用：

```text
propose_claude_evolution(write_drafts=true)
```

它会基于契约检查结果生成：

- 该补什么 frontmatter
- 该补哪些关键契约词
- 哪些命令要补上下游承接
- 哪些模板要补数据库协作验证或 feedback 闭环

这些提案同样只会落草稿，不会直接覆盖正式 `.claude` 文件。

如需继续把提案收敛成结构化 patch plan，可调用：

```text
plan_claude_patches(write_drafts=true)
```

它生成的是“怎么改、改哪里、锚点大概在哪、建议样例是什么”，适合后续继续人工吸收，或作为更严格自动化的上游输入。

如需继续把 patch plan 落成基于当前文件内容的 patch draft，可调用：

```text
draft_claude_patches(write_drafts=true)
```

这一步会同时给出：

- 当前文件相关片段
- 建议插入或改写后的草稿片段
- 锚点建议

它适合人工 review 之后再决定是否吸收进正式 `.claude` 文件。

6. 后续 `.claude` 侧演化结果都必须先落草稿，再由现有流程吸收

## `.claude` 兼容能力的完整使用方式

下面这套流程更适合已经落地 `.claude` 团队共享系统的项目，例如：

- `cfs-report`
- `cfs-finance`
- `cfs-pay-rec`

### 1. 项目准备

你的项目根目录下需要真实存在：

```text
.claude/
```

并且至少建议有这些正式文件：

```text
.claude/CLAUDE.md
.claude/PRD.md
.claude/prime-context.md
.claude/validation-context.md
.claude/reference/
.claude/templates/
.claude/commands/
```

### 2. 打开 `.claude` 兼容能力

至少打开：

```bash
OPENSPACE_WORKSPACE=/path/to/project
OPENSPACE_ENABLE_CLAUDE_EVOLUTION=true
```

如果还要启用生命周期治理：

```bash
OPENSPACE_ENABLE_CLAUDE_DEPRECATION=true
OPENSPACE_ENABLE_SKILL_DEPRECATION=true
```

### 3. 启动后会发生什么

OpenSpace 检测到 `.claude` 后，会自动准备：

```text
.claude/evolution-drafts/
.openspace/lifecycle/lifecycle.json
```

其中：

- `.claude/evolution-drafts/`
  - 放 `.claude` 侧所有自动演化草稿
- `.openspace/lifecycle/lifecycle.json`
  - 放原生 skill 和 `.claude` artifact 的生命周期状态

### 4. `.claude` 常用 MCP 工具

#### `analyze_claude_artifacts`

作用：

- 检查 `.claude` 当前正式文件有没有契约漂移
- 只做检查，不直接改文件

示例：

```text
analyze_claude_artifacts(write_drafts=true)
```

输出：

- evaluation 结果
- 如开启 `write_drafts=true`，写入 `evolution-drafts/*-evaluation.draft.md`

#### `propose_claude_evolution`

作用：

- 基于 evaluation 结果给出修复提案

示例：

```text
propose_claude_evolution(write_drafts=true)
```

输出：

- proposal 结果
- 写入 `*-proposal.draft.md`

#### `plan_claude_patches`

作用：

- 把 proposal 收敛成结构化 patch plan

示例：

```text
plan_claude_patches(write_drafts=true)
```

输出：

- patch step
- 写入 `*-patch-plan.draft.md`

#### `draft_claude_patches`

作用：

- 结合当前正式文件内容，生成更接近实际 Markdown 修改的草稿

示例：

```text
draft_claude_patches(write_drafts=true)
```

输出：

- 当前片段
- 建议片段
- 锚点建议
- 写入 `*-patch-draft.draft.md`

### 5. 草稿目录怎么看

默认目录结构：

```text
.claude/evolution-drafts/
  commands/
  templates/
  reference/
  memory/
  reports/
```

含义：

- `commands/`
  - 命令类草稿
- `templates/`
  - 模板类草稿
- `reference/`
  - 知识卡片、knowledge-index、knowledge-feedback 相关草稿
- `memory/`
  - `CLAUDE.md / PRD.md / prime-context.md / validation-context.md`
- `reports/`
  - 生命周期报告、退役建议、汇总类报告

### 6. 推荐吸收方式

`.claude` 侧草稿不是自动正式生效的，推荐还是回到你原本的团队流程中吸收：

- 先人工看 `evaluation / proposal`
- 再看 `patch-plan / patch-draft`
- 再通过你现有流程决定是否吸收：
  - `/xrep`
  - `/srev`
  - `/cmit`
  - 或人工直接合并

### 7. 适合用来演化什么

当前更适合演化的是：

- `.claude/commands/*.md`
  - 闭环、下一步、抗幻觉规则、上下游承接
- `.claude/templates/*.md`
  - 模板漂移、与上下游命令协同、生成后职责是否匹配
- `.claude/reference/*.md`
  - 长期知识卡片、索引、反馈闭环
- 正式记忆
  - `CLAUDE.md / PRD.md / prime-context.md / validation-context.md`

### 8. 不该怎么用

不要把它当作“自动重写 `.claude` 正式文件”的工具。

当前正确用法是：

- 先让它检查
- 再让它产出草稿
- 再由团队流程决定吸收

## `.claude` 兼容能力的使用原则

启用 `.claude` 兼容后，系统仍然遵循以下边界：

### 1. 不直接改正式文件

不会自动直接覆盖：

- `.claude/commands/**/*.md`
- `.claude/templates/*.md`
- `.claude/reference/*.md`
- `CLAUDE.md`
- `PRD.md`
- `prime-context.md`
- `validation-context.md`

### 2. 统一先出草稿

草稿统一输出到：

```text
.claude/evolution-drafts/
```

### 3. 正式吸收仍由团队流程控制

建议通过你现有的 `.claude` 流程吸收：

- `/xrep`
- `/srev`
- `/cmit`
- 或人工审阅

### 4. 不能影响原生 skill

`.claude` 兼容能力必须是旁路扩展：

- 不改变原生 `SKILL.md` 检索语义
- 不改变原生 `FIX / DERIVED / CAPTURED`
- 不让 `.claude` Artifact 污染 skill registry 的默认逻辑

## `.claude` 兼容后主要处理什么

### 命令

处理：

- 职责冲突
- 闭环缺失
- 幻觉提示
- 项目串味
- 上下游命令承接关系

### 模板

处理：

- 模板与正式文件漂移
- 模板生成后是否符合职责
- 是否适合被上下游命令消费

### reference

处理：

- 普通知识卡片
- `knowledge-index.md`
- `knowledge-feedback.md`
- `_knowledge-template.md`

### 正式记忆

处理：

- `CLAUDE.md`
- `PRD.md`
- `prime-context.md`
- `validation-context.md`

## 关于退役机制

本项目支持为以下对象预留退役机制：

- 原生 skill
- `command_alias`
- `command_workflow`
- `claude_template`
- `reference_card`

但退役必须遵循硬标准：

- 固定任务集
- 固定评分器
- 固定阈值
- 两阶段验证

不会因为“感觉模型更强了”就直接退役。

## 本地开发

```bash
git clone https://github.com/UF-gzj/openspace-claude-evolution.git
cd openspace-claude-evolution
python -m pip install -e .[dev]
```

建议开发时至少准备一个带 `.claude/` 的真实项目作为回归样本，例如：

- `cfs-report`
- `cfs-finance`

## 常见问题

### 1. 为什么我没有配置 `OPENSPACE_LLM_*` 也能跑

因为本项目支持复用本机 Claude Code 配置。如果你的 Claude Code 已经登录，OpenSpace 会尝试读取 `~/.claude/settings.json`。

### 2. 为什么 `.claude` 没有生成草稿

先检查：

- `OPENSPACE_WORKSPACE` 是否指向正确项目根目录
- 该目录下是否真实存在 `.claude/`
- 是否启用了 `OPENSPACE_ENABLE_CLAUDE_EVOLUTION=true`
- MCP 调用时是否传了 `write_drafts=true`

### 3. 为什么有些 `.claude` 文件没有 proposal / patch draft

因为当前实现是契约驱动的。没有问题的文件只会有 evaluation，不会强行生成 proposal。

### 4. 为什么我看到的只是草稿，不是正式修改

这是设计要求，不是缺功能。当前 `.claude` 兼容能力默认只出草稿，避免把团队正式规则直接改坏。

### 5. 为什么不建议直接启用云社区

因为这个改造版默认服务团队内、公司内项目，优先保证私有化、可控和审计边界。

## 许可证与来源

本项目基于香港大学开源项目 OpenSpace 改造，保留 MIT License。

- 原始项目：<https://github.com/HKUDS/OpenSpace>
- 当前改造仓库：<https://github.com/UF-gzj/openspace-claude-evolution>

维护说明：

- 原始能力与基础架构来源于 OpenSpace
- `.claude` 团队共享系统兼容、草稿演化、生命周期治理设计由关镇江推进
