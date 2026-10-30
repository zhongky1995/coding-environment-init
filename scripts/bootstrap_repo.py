#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
import re
import sys


IGNORE_DIRS = {
    ".git",
    ".idea",
    ".next",
    ".nuxt",
    ".turbo",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
}

EXISTING_MARKERS = {
    "app",
    "backend",
    "cloudflare",
    "frontend",
    "package.json",
    "pages",
    "pyproject.toml",
    "server",
    "src",
    "tests",
    "vite.config.ts",
    "web",
}

MINIMAL_DIRS = ["docs/ai"]

GUIDED_DIRS = ["docs/plan"]

EXPANDED_DIRS = [
    "docs/context",
    "docs/prd",
    "docs/architecture",
    "docs/qa",
]

LAYERED_CODE_DIRS = [
    "src/modules",
    "src/shared",
    "src/workflows",
    "src/contracts",
    "tests",
    "scripts",
]


@dataclass
class WriteResult:
    created: list[str]
    skipped: list[str]
    overwritten: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap a coding environment scaffold that constrains AI attention.",
    )
    parser.add_argument("project_root", help="Target project root")
    parser.add_argument(
        "--project-name",
        help="Human-readable project name. Defaults to the root directory name.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "greenfield", "existing"],
        default="auto",
        help="Repo mode. Defaults to auto detection.",
    )
    parser.add_argument(
        "--preset",
        choices=["minimal", "guided", "expanded"],
        default="minimal",
        help="Scaffold preset. Defaults to minimal for compatibility. Use guided for day-to-day AI coding.",
    )
    parser.add_argument(
        "--code-layout",
        choices=["none", "layered"],
        default="none",
        help="Optional extra code scaffold. Defaults to none.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite files that already exist.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "project"


def detect_mode(project_root: Path) -> str:
    for marker in EXISTING_MARKERS:
        if (project_root / marker).exists():
            return "existing"
    # Unknown non-document content is not evidence of a greenfield repository.
    for entry in project_root.iterdir():
        if entry.name in IGNORE_DIRS or entry.name in {"docs", "AGENTS.md", ".gitignore"}:
            continue
        if entry.is_file() and entry.suffix.lower() in {".md", ".txt", ".rst"}:
            continue
        return "existing"
    return "greenfield"


def load_template(skill_root: Path, relative_path: str) -> str:
    template_path = skill_root / "assets" / "templates" / relative_path
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text()


def render_template(template: str, variables: dict[str, str]) -> str:
    content = template
    for key, value in variables.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def visible_root_entries(project_root: Path) -> tuple[list[Path], list[Path]]:
    dirs: list[Path] = []
    files: list[Path] = []
    for entry in sorted(project_root.iterdir(), key=lambda item: item.name.lower()):
        if entry.name in IGNORE_DIRS:
            continue
        if entry.name.startswith(".") and entry.name not in {".gitignore"}:
            continue
        if entry.is_dir():
            dirs.append(entry)
        else:
            files.append(entry)
    return dirs, files


def iter_child_names(directory: Path) -> Iterable[str]:
    count = 0
    for entry in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
        if entry.name in IGNORE_DIRS:
            continue
        if entry.name.startswith("."):
            continue
        yield f"{entry.name}/" if entry.is_dir() else entry.name
        count += 1
        if count >= 8:
            break


def list_markdown_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.md") if path.is_file())


def ensure_directories(project_root: Path, relative_dirs: list[str]) -> list[str]:
    created: list[str] = []
    for relative_dir in relative_dirs:
        target = project_root / relative_dir
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created.append(relative_dir)
    return created


def write_file(
    project_root: Path,
    target: Path,
    content: str,
    force: bool,
    result: WriteResult,
) -> None:
    relative = target.relative_to(project_root).as_posix()
    if target.exists() and not force:
        result.skipped.append(relative)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        result.overwritten.append(relative)
    else:
        result.created.append(relative)
    target.write_text(content)


def should_seed_doc(project_root: Path, relative_dir: str) -> bool:
    return not list_markdown_files(project_root / relative_dir)


def top_level_directory_lines(project_root: Path) -> list[str]:
    dirs, _ = visible_root_entries(project_root)
    if not dirs:
        return ["- 当前顶层暂无可见目录。"]

    lines: list[str] = []
    for directory in dirs[:12]:
        children = ", ".join(iter_child_names(directory))
        if children:
            lines.append(f"- `{directory.name}/` -> {children}")
        else:
            lines.append(f"- `{directory.name}/`")
    return lines


def top_level_file_lines(project_root: Path) -> list[str]:
    _, files = visible_root_entries(project_root)
    if not files:
        return ["- 当前顶层暂无关键文件。"]
    return [f"- `{file_path.name}`" for file_path in files[:16]]


def format_doc_list(project_root: Path, paths: list[Path]) -> str:
    if not paths:
        return "未发现"
    labels = [f"`{path.relative_to(project_root).as_posix()}`" for path in paths[:4]]
    if len(paths) > 4:
        labels.append("...")
    return "，".join(labels)


def project_context_content(
    skill_root: Path,
    project_root: Path,
    mode: str,
    variables: dict[str, str],
) -> str:
    template = load_template(skill_root, "docs/ai/project-context.md")
    project_vars = dict(variables)
    project_vars.update(
        {
            "MODE": mode,
            "PROJECT_ROOT": project_root.as_posix(),
            "REPO_SNAPSHOT": "\n".join(top_level_directory_lines(project_root)),
            "TOP_FILES": "\n".join(top_level_file_lines(project_root)),
        }
    )
    return render_template(template, project_vars)


def repo_map_content(project_root: Path, project_name: str, mode: str, execution_record: str) -> str:
    ai_files = list_markdown_files(project_root / "docs" / "ai")
    prd_files = list_markdown_files(project_root / "docs" / "prd")
    arch_files = list_markdown_files(project_root / "docs" / "architecture")
    plan_files = list_markdown_files(project_root / "docs" / "plan")
    qa_files = list_markdown_files(project_root / "docs" / "qa")

    lines = [
        f"# {project_name} 仓库地图",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 仓库模式：`{mode}`",
        f"- 项目根目录：`{project_root}`",
        "",
        "## 顶层目录快照",
        "",
        *top_level_directory_lines(project_root),
        "",
        "## 顶层关键文件",
        "",
        *top_level_file_lines(project_root),
        "",
        "## 已存在的治理文档",
        "",
        f"- AI 入口：{format_doc_list(project_root, ai_files)}",
        f"- PRD：{format_doc_list(project_root, prd_files)}",
        f"- 架构：{format_doc_list(project_root, arch_files)}",
        f"- 计划：{format_doc_list(project_root, plan_files)}",
        f"- QA：{format_doc_list(project_root, qa_files)}",
        "",
        "## 初始化后建议",
        "",
        "- 从 `docs/ai/project-context.md` 定位整体目标、有效设计及依据、当前成果。",
        "- 核对 `docs/ai/current-task.md` 怎样服务整体目标，再读本轮范围和完成标准。",
        "- 再读 `docs/ai/architecture-guardrails.md`，确认本轮不会破坏边界。",
        f"- 执行记录：{execution_record}；不重复维护状态。",
        "- 先解决影响当前交付的未知，按需读取详细文档，不以所有空表填满作为开工条件。",
    ]
    return "\n".join(lines) + "\n"


def bootstrap_minimal(
    project_root: Path,
    skill_root: Path,
    mode: str,
    variables: dict[str, str],
    force: bool,
    result: WriteResult,
) -> list[str]:
    created_dirs = ensure_directories(project_root, MINIMAL_DIRS)

    current_task_template = load_template(skill_root, "docs/ai/current-task.md")
    architecture_template = load_template(skill_root, "docs/ai/architecture-guardrails.md")

    write_file(
        project_root,
        project_root / "docs/ai/current-task.md",
        render_template(current_task_template, variables),
        force,
        result,
    )
    write_file(
        project_root,
        project_root / "docs/ai/architecture-guardrails.md",
        render_template(architecture_template, variables),
        force,
        result,
    )
    write_file(
        project_root,
        project_root / "docs/ai/project-context.md",
        project_context_content(skill_root, project_root, mode, variables),
        force,
        result,
    )

    return created_dirs


def bootstrap_guided(
    project_root: Path,
    skill_root: Path,
    mode: str,
    variables: dict[str, str],
    force: bool,
    result: WriteResult,
) -> list[str]:
    created_dirs = bootstrap_minimal(
        project_root,
        skill_root,
        mode,
        variables,
        force,
        result,
    )
    created_dirs.extend(ensure_directories(project_root, GUIDED_DIRS))

    current_todo_template = load_template(skill_root, "docs/plan/current-todo.md")
    write_file(
        project_root,
        project_root / "docs/plan/current-todo.md",
        render_template(current_todo_template, variables),
        force,
        result,
    )

    return created_dirs


def bootstrap_expanded(
    project_root: Path,
    skill_root: Path,
    project_name: str,
    mode: str,
    variables: dict[str, str],
    force: bool,
    result: WriteResult,
) -> list[str]:
    created_dirs = bootstrap_guided(
        project_root,
        skill_root,
        mode,
        variables,
        force,
        result,
    )
    created_dirs.extend(ensure_directories(project_root, EXPANDED_DIRS))

    always_seed = {
        "docs/qa/current-qa-checklist.md": "docs/qa/current-qa-checklist.md",
    }

    for relative_path, template_key in always_seed.items():
        template = load_template(skill_root, template_key)
        write_file(
            project_root,
            project_root / relative_path,
            render_template(template, variables),
            force,
            result,
        )

    conditional_templates = [
        ("docs/prd", "docs/prd/current-prd.md"),
        ("docs/architecture", "docs/architecture/current-architecture.md"),
    ]
    for relative_dir, template_key in conditional_templates:
        if should_seed_doc(project_root, relative_dir):
            template = load_template(skill_root, template_key)
            target = project_root / template_key
            write_file(
                project_root,
                target,
                render_template(template, variables),
                force,
                result,
            )

    write_file(
        project_root,
        project_root / "docs/context/repo-map.md",
        repo_map_content(project_root, project_name, mode, variables["EXECUTION_RECORD"]),
        force,
        result,
    )

    return created_dirs


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"[ERROR] Project root does not exist: {project_root}")
        return 1
    if not project_root.is_dir():
        print(f"[ERROR] Project root is not a directory: {project_root}")
        return 1

    detected_mode = detect_mode(project_root)
    mode = detected_mode if args.mode == "auto" else args.mode
    if args.code_layout == "layered" and (mode != "greenfield" or detected_mode != "greenfield"):
        print("[ERROR] Layered code layout requires a verified greenfield directory; no files changed.")
        return 1

    project_name = args.project_name or project_root.name
    project_slug = slugify(project_name)
    today = datetime.now().strftime("%Y-%m-%d")
    skill_root = Path(__file__).resolve().parent.parent

    result = WriteResult(created=[], skipped=[], overwritten=[])
    variables = {
        "DATE": today,
        "PROJECT_NAME": project_name,
        "PROJECT_SLUG": project_slug,
        "EXECUTION_RECORD": (
            "本文件「执行现场与交接」"
            if args.preset == "minimal"
            else "`docs/plan/current-todo.md`"
        ),
        "LOCAL_EXECUTION_SECTION": (
            "## 执行现场与交接\n\n"
            "- 当前步骤/状态：\n"
            "- 工作目录、分支/提交或快照、未提交改动与归属：\n"
            "- 已完成/未完成、相关基线与已有失败：\n"
            "- 验证：验收 ID、代码版本、环境/数据、操作、结果、证据位置：\n"
            "- 决策与失败尝试的证据：\n"
            "- 下一具体动作与需读文件：\n"
            "- 当前阻塞与恢复安排（适用时）：\n"
            if args.preset == "minimal"
            else ""
        ),
    }

    if args.preset == "minimal":
        created_dirs = bootstrap_minimal(
            project_root,
            skill_root,
            mode,
            variables,
            args.force,
            result,
        )
    elif args.preset == "guided":
        created_dirs = bootstrap_guided(
            project_root,
            skill_root,
            mode,
            variables,
            args.force,
            result,
        )
    else:
        created_dirs = bootstrap_expanded(
            project_root,
            skill_root,
            project_name,
            mode,
            variables,
            args.force,
            result,
        )

    if args.code_layout == "layered":
        created_dirs.extend(ensure_directories(project_root, LAYERED_CODE_DIRS))

    print("")
    print("[OK] Documentation scaffold created; repository readiness has not been verified")
    print(f"[INFO] Mode: {mode}")
    print(f"[INFO] Preset: {args.preset}")
    print(f"[INFO] Project: {project_name}")
    print("")

    if created_dirs:
        print("[DIR] Created directories:")
        for relative_dir in created_dirs:
            print(f"  - {relative_dir}")
        print("")

    if result.created:
        print("[FILE] Created files:")
        for path in result.created:
            print(f"  - {path}")
        print("")

    if result.overwritten:
        print("[FILE] Overwritten files:")
        for path in result.overwritten:
            print(f"  - {path}")
        print("")

    if result.skipped:
        print("[FILE] Skipped existing files:")
        for path in result.skipped:
            print(f"  - {path}")
        print("")

    if args.preset == "minimal":
        print("[NEXT] Complete the current deliverable and repository preparation; file creation alone is not readiness.")
    elif args.preset == "guided":
        print("[NEXT] Complete pre-development decisions and runnable repository preparation; record evidence in project-context and current-todo.")
    else:
        print("[NEXT] Fill the current deliverable and execution record; resolve only the unknowns that affect this batch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
