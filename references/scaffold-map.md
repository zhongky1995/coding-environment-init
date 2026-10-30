# 生成物与迁移

本页与脚本仅用于软件开发分支。客户建档、资料归档及长期交付工作区按 [客户交付初始化](client-delivery-init.md) 处理，不套用下表的开发模板。

脚本在本技能的 scripts/bootstrap_repo.py。它创建缺失文档，可按显式选项补通用代码目录；不执行 Git、依赖安装、环境配置或运行验证。开发初始化由 Agent 按 repository-setup.md 完成，不能把脚本成功当准备就绪。

| preset | 新空目录中的文档 |
|---|---|
| minimal（CLI 默认） | docs/ai/project-context.md、architecture-guardrails.md、current-task.md |
| guided（日常推荐） | minimal + docs/plan/current-todo.md |
| expanded | guided + docs/context/repo-map.md、docs/prd/current-prd.md、docs/architecture/current-architecture.md、docs/qa/current-qa-checklist.md |

已有目标文件默认保留。expanded 的 PRD 或 architecture 目录已有 Markdown 时不另建对应默认文件；其他位置同义文档需 Agent 先识别并直接引用，不为选档复制另一套。

## 文档职责与迁移

minimal → guided：把步骤、现场/验证迁到 current-todo，current-task 留执行记录链接。脚本不自动移动用户正文。

已有 requirements/design/acceptance/plan/progress 等体系时保留其命名，建立对应入口。每项状态只维护一处；需要摘要时链接原始记录并注明时效。

重跑保留旧文件；升级正文使用局部编辑。--force 会覆盖目标，只在用户明确要求重建且内容可覆盖时使用，不用于日常升级。PRD/architecture 的同目录已有文档保护仍生效。

## AI 入口与实际环境

脚本不修改 AGENTS。Agent 读现行规则后补短导航；新项目按所用工具约定建立必要入口，不复制多份相同家规。

版本记录、忽略规则、框架入口、锁文件、配置示例、测试身份、启动与检查由仓库准备流程负责。project-context 承接准备状态与证据，current-task 给出能否开工的结论。

## 可选通用代码目录

优先采用已选框架惯例。仅用户明确需要、确为绿地且无既定框架布局时使用 --mode greenfield --code-layout layered：

```text
src/modules/
src/shared/
src/workflows/
src/contracts/
tests/
scripts/
```

已有代码/技术栈或不明非文档内容按 existing；显式 greenfield 不绕过保护。默认不添加业务目录，不安装依赖或触发外部调用。
