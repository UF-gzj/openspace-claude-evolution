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

## 演化原理

### 原生 skill 如何优化或生成

OpenSpace 原生的 `SKILL.md` 演化，默认不是从 skill 市场直接拉取一份来替换本地 skill。

它的主路径是：

1. 先执行真实任务
2. 记录执行过程、skill 命中情况、fallback、完成结果
3. 由执行后分析器判断是否存在可演化机会
4. 再由大模型结合当前 skill 内容、最近执行分析、工具问题和指标数据，生成：
   - `FIX`
   - `DERIVED`
   - `CAPTURED`
5. 把结果写回本地 skill 目录，并保留 lineage / version / store 记录

也就是说：

- **skill 优化/生成的主路径，是依赖大模型在本地证据基础上写出新版本**
- **不是默认从 skill 市场直接拉取来替换**

skill 市场的作用更偏：

- `search_skills`
  - 搜索可安装 skill
- `download_skill`
  - 人工或显式流程拉取外部 skill

它属于“外部补充来源”，不是本地 skill 自动演化的主机制。

### `.claude` 如何优化

`.claude` 兼容能力和原生 skill 不同，它现在走的是 **显式触发 + 草稿优先** 的治理式演化。

主路径是：

1. 显式调用：
   - `analyze_claude_artifacts`
   - `propose_claude_evolution`
   - `plan_claude_patches`
   - `draft_claude_patches`
2. 先做静态契约检查
3. 再结合项目真实代码和配置事实做二次审核
4. 只生成：
   - evaluation
   - proposal
   - patch plan
   - patch draft
5. 草稿统一写入 `.claude/evolution-drafts/`
6. 不直接覆盖正式 `.claude` 文件

也就是说：

- **`.claude` 优化不是自动改正式规则**
- **而是基于工作区事实生成可审阅草稿**
- **吸收是否生效，仍由团队流程或人工决定**

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

### 2.1 `.claude` 审核的两层逻辑

`.claude` 兼容能力采用两层审核，而不是只靠模板检查：

1. 静态契约检查
- 只负责低风险骨架检查
- 只检查 frontmatter、最低结构、最低承接关系、知识闭环入口
- 不直接决定项目个性化内容应该怎么写

2. 项目代码事实审核
- 在静态检查之后，再结合当前项目目录、模块、配置文件、测试现实等代码事实做二次审核
- 决定：
  - 哪些 MD 真有问题
  - 这些 MD 应该怎么改
  - 这些 MD 具体改哪里
  - 草稿是否贴近当前项目本身

设计边界：

- 第一层不能覆盖项目个性化内容
- 第二层才负责产出项目级建议
- 如果静态契约建议和代码事实冲突，以代码事实为准

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

## 启动 Dashboard 可视化页面

本项目除了 MCP 服务，还内置了一个独立的 dashboard 服务。

启动方式：

```bash
python -m openspace.dashboard_server --host 127.0.0.1 --port 7788
```

启动后默认访问：

```text
http://127.0.0.1:7788
```

说明：

- dashboard 与 MCP 服务是两条独立入口
- MCP 负责工具调用与演化执行
- dashboard 负责查看原生 skill、workflow，以及 `.claude` 兼容能力的可视化状态

如果你希望 dashboard 直接展示某个项目的 `.claude` 数据，启动前请先设置：

```bash
OPENSPACE_WORKSPACE=D:/Desktop/cfs-report
```

当前 dashboard 已支持展示：

- 原生 OpenSpace `skills`
- 原生 `workflows`
- `.claude` artifact 盘点
- `.claude/evolution-drafts/` 草稿统计与最近草稿
- `.claude` lifecycle 状态

如果没有提前构建前端，dashboard 根路径只会返回 API 提示。完整页面需要先执行：

```bash
cd frontend
npm install
npm run build
```

构建完成后，`frontend/dist` 会被 dashboard 服务直接托管。

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

## 如何 100% 触发 `.claude` 检测与升级

如果你希望 OpenSpace **明确**对 `.claude` 生成检测结果、修复提案、patch plan 或 patch draft，请按下面的顺序执行。

### 第一步：明确工作区

工作区必须是真实项目根目录，并且该目录下存在 `.claude/`：

```bash
OPENSPACE_WORKSPACE=D:/Desktop/cfs-report
```

### 第二步：显式开启 `.claude` 兼容

至少开启：

```bash
OPENSPACE_ENABLE_CLAUDE_EVOLUTION=true
```

如果还要启用 `.claude` 生命周期治理，可再加：

```bash
OPENSPACE_ENABLE_CLAUDE_DEPRECATION=true
```

### 第三步：启动 MCP 服务

```bash
python -m openspace.mcp_server
```

### 第四步：显式调用 `.claude` 工具

只有真正调用下面 4 个工具之一，才会进入 `.claude` 演化链路：

- `analyze_claude_artifacts`
- `propose_claude_evolution`
- `plan_claude_patches`
- `draft_claude_patches`

它们分别对应：

1. `analyze_claude_artifacts`
- 检查哪些 `.claude` MD 有问题
- 输出 evaluation 草稿

2. `propose_claude_evolution`
- 基于检查结果生成修复提案
- 输出 proposal 草稿

3. `plan_claude_patches`
- 把提案变成结构化 patch 计划
- 输出 patch-plan 草稿

4. `draft_claude_patches`
- 生成可审阅的 Markdown patch 草稿
- 输出 patch-draft 草稿

### 一句话顺序触发

如果你希望按完整顺序一次走完 `.claude` 的四层链路，最直接的做法是按下面这一句依次执行：

```text
analyze_claude_artifacts(write_drafts=true) -> propose_claude_evolution(write_drafts=true) -> plan_claude_patches(write_drafts=true) -> draft_claude_patches(write_drafts=true)
```

推荐使用场景：

- 你刚完成一轮 `.claude` 体系审查
- 你已经确认要让 OpenSpace 为当前工作区生成完整草稿
- 你希望一次性拿到：
  - evaluation
  - proposal
  - patch plan
  - patch draft

不推荐使用场景：

- 你只想先看有没有问题
- 你还没确定是否需要生成草稿
- 你只想审一个单独层级（例如只看 proposal）

### 第五步：确认写草稿

如果调用时 `write_drafts=true`，草稿会写到：

```text
.claude/evolution-drafts/
```

如果 `write_drafts=false`，工具只返回分析/提案结果，不写草稿文件。

### 不会自动触发的场景

下面这些场景**不会**自动触发 `.claude` 升级：

- 正常执行 `execute_task`
- 原生 skill 的 `FIX / DERIVED / CAPTURED`
- 只是使用项目里的 `/prim /pln /vald` 等 `.claude` 命令
- 只是打开 dashboard 页面
- dashboard 读取 `.claude` 数据

也就是说：

- `.claude` 检测/升级是**显式触发**
- 不是“用了 `.claude` 命令以后自动改 `.claude`”
- 所有正式文件改动仍需要人工审阅后再吸收

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

如需真正生成 `.claude` 草稿，直接回到前面的 [如何 100% 触发 `.claude` 检测与升级](#如何-100-触发-claude-检测与升级) 执行即可。

这里记住一条就够了：

```text
analyze_claude_artifacts(write_drafts=true) -> propose_claude_evolution(write_drafts=true) -> plan_claude_patches(write_drafts=true) -> draft_claude_patches(write_drafts=true)
```

输出仍然统一写入：

```text
.claude/evolution-drafts/commands/
.claude/evolution-drafts/templates/
.claude/evolution-drafts/reference/
.claude/evolution-drafts/memory/
```

后续 `.claude` 侧结果都必须先看草稿，再由现有流程吸收。

## `.claude` 兼容能力的完整使用方式

下面这套流程更适合已经落地 `.claude` 团队共享系统的项目，例如：

- `cfs-report`
- `cfs-finance`
- `cfs-pay-rec`

完整前置条件、开关和四个工具的分层说明，已经在前面的 [如何 100% 触发 `.claude` 检测与升级](#如何-100-触发-claude-检测与升级) 里写全了。这里不再重复解释同一套步骤，只保留真正补充使用时会关心的内容。

### 1. 启用后会新增什么

当工作区下存在 `.claude/`，并且显式开启 `.claude` 兼容后，OpenSpace 会准备：

```text
.claude/evolution-drafts/
.openspace/lifecycle/lifecycle.json
```

其中：

- `.claude/evolution-drafts/`
  - 放 `.claude` 侧所有自动演化草稿
- `.openspace/lifecycle/lifecycle.json`
  - 放原生 skill 和 `.claude` artifact 的生命周期状态

### 2. 草稿目录怎么看

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

### 3. 推荐吸收方式

`.claude` 侧草稿不是自动正式生效的，推荐还是回到你原本的团队流程中吸收：

- 先人工看 `evaluation / proposal`
- 再看 `patch-plan / patch-draft`
- 再通过你现有流程决定是否吸收：
  - `/xrep`
  - `/srev`
  - `/cmit`
  - 或人工直接合并

### 4. 适合用来演化什么

当前更适合演化的是：

- `.claude/commands/*.md`
  - 闭环、下一步、抗幻觉规则、上下游承接
- `.claude/templates/*.md`
  - 模板漂移、与上下游命令协同、生成后职责是否匹配
- `.claude/reference/*.md`
  - 长期知识卡片、索引、反馈闭环
- 正式记忆
  - `CLAUDE.md / PRD.md / prime-context.md / validation-context.md`

### 5. 不该怎么用

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
