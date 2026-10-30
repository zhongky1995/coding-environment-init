# coding-environment-init

一个用于初始化、接手和持续维护项目工作区的 Codex skill。支持软件开发，也支持客户交付、咨询、方案和内容项目。

它让项目的整体目标、有效设计及决定依据、当前成果和接手入口能够跨对话延续，减少单个对话把临时理解写成新基准的风险。

A Codex skill for project workspace initialization and continuity: preserve project goals, effective designs, decision provenance, current artifacts, and handoff entry points across conversations.

## 能做什么

- **持续维护与接手**：复用已有项目记录，让 AGENTS 指向整体目标、有效设计、当前成果和任务；核对本轮工作与整体方向的关系。
- **维护变更依据**：区分用户决定、授权内的专业选择、已核实事实和待验证方案；保留变化理由、适用范围与未解决偏差。
- **客户交付建档**：读懂合同、方案和沟通材料，整理有效范围、资料来源、工作线及新资料入口。
- **软件开工准备**：核对仓库现场、开发条件、运行入口及验证证据，只补实际缺口。

已有文档和目录可以继续使用，不要求另建一套项目管理文件。完整说明见 [SKILL.md](SKILL.md)。

## 安装

将本仓库放入 Codex 的 skills 目录。macOS / Linux 示例：

```bash
git clone https://github.com/zhongky1995/coding-environment-init.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/coding-environment-init"
```

已有同名技能时，先保留本地修改，再比较合并；不要直接覆盖。安装后在新对话中调用。

## 使用示例

### 维护已有项目

```text
使用 $coding-environment-init 接手这个项目。
沿用已有目录，核对整体目标、有效设计与当前成果，修复必要的 AGENTS 接手入口。
本轮任务是……，保留尚未解决的偏差及决定来源。
```

### 建立客户交付工作区

```text
使用 $coding-environment-init 整理这些合同、方案与会议资料，
建立可持续承接咨询和开发工作的项目入口，留好新资料接收位置。
```

### 准备软件开发

```text
使用 $coding-environment-init 接手这个代码仓库，
准备本轮功能所需的运行条件并验证可启动，已有文档直接复用。
```

技能会按当前交付选择分支。未来可能开发软件，不要求本轮就准备开发环境。

## 文件说明

| 路径 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 技能入口与场景选择 |
| [references/](references/) | 项目维护、交付建档、开发准备和接续规则 |
| [agents/openai.yaml](agents/openai.yaml) | Codex 技能展示与调用说明 |
| [assets/templates/](assets/templates/) | 可选开发文档模板 |
| [scripts/bootstrap_repo.py](scripts/bootstrap_repo.py) | 仅生成缺失的开发文档骨架 |
| [tests/](tests/) | 文档生成器的行为回归测试 |

开发分支需要生成骨架时，可在本仓库中运行（Python 3.12）：

```bash
python3 scripts/bootstrap_repo.py /path/to/project --preset guided
```

脚本默认保留已有目标文件，不修改 AGENTS，也不执行 Git 初始化、依赖安装或运行验证。已有等价文档时，由 Agent 直接维护，无需运行脚本。

## 能力边界与验证

这是指导 Agent 工作和维护依据的技能。它依赖模型理解来源与成果，无法从技术上阻止越权改写，也不能保证自动发现所有整体偏差。项目是否真正兑现目标，仍须结合实际成果判断。

运行现有回归测试：

```bash
python3 -m unittest discover -s tests
```

测试检查生成器行为，包括默认文件数量、模板替换、保留已有内容和绿地目录保护，并检查技能说明中的本地文件引用（不检查生成模板的目标或章节锚点）。这些检查适用于本技能包，不是给所有项目注入的通用门禁，也不代表整体方向判断能力已经通过验证。GitHub Actions 会运行测试与 Python 语法检查。

## 许可证

[MIT](LICENSE)。
