"""Prepare AnYanEval tasks, aggregate independent grades, and verify published results."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import statistics
import subprocess


ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "benchmark/tasks.json"
RUBRIC = ROOT / "benchmark/rubric.json"
RESULT = ROOT / "results/qwen3.8-flash-next.json"
PROMPT_HEADER = (
    "在当前评测工作区完成本题。输出需要交付的产物，使用本机已有工具。"
    "题目素材均为合成数据或明确提供的固定文件。\n\n"
)


def read(path):
    return json.loads(path.read_bytes())


def index(suite, rubric):
    if suite["version"] != rubric["suite_version"] or suite["maximum_score"] != 100:
        raise ValueError("Version or scale differs")
    dimensions = suite["dimensions"]
    if len(dimensions) != 10 or len({row["name"] for row in dimensions}) != 10:
        raise ValueError("Expected ten distinct dimensions")
    tasks = {}
    for dim in dimensions:
        items = dim["tasks"]
        if not 1 <= len(items) <= 2 or sum(task["max_points"] for task in items) != 10:
            raise ValueError(f"Wrong point budget for {dim['name']}")
        for task in items:
            if task["id"] in tasks:
                raise ValueError(f"Duplicate task {task['id']}")
            tasks[task["id"]] = task
    rules = {rule["task_id"]: rule for rule in rubric["rubrics"]}
    if rules.keys() != tasks.keys() or len(rules) != len(rubric["rubrics"]):
        raise ValueError("Question and rubric IDs differ")
    for task_id, rule in rules.items():
        criteria = rule["criteria"]
        if (rule["max_points"] != tasks[task_id]["max_points"]
                or sum(c["points"] for c in criteria) != rule["max_points"]
                or len({c["id"] for c in criteria}) != len(criteria)):
            raise ValueError(f"Invalid rubric totals for {task_id}")
    return tasks, rules


def write_fixtures(workspace, files, seed):
    targets = []
    for name, content in files.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts or "\\" in name:
            raise ValueError(f"Invalid fixture path {name!r}")
        target = workspace.joinpath(*relative.parts)
        if not target.resolve().is_relative_to(workspace) or target.exists() or target.is_symlink():
            raise ValueError(f"Fixture would overwrite or escape the workspace: {name!r}")
        targets.append((target, content.replace("<SEED>", str(seed))))
    for path, content in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as file:
            file.write(content)


def prepare(task, args, cap):
    workspace = args.workspace.resolve()
    prompt_path = args.prompt_out.resolve()
    turns = task.get("turns") or [{"turn": task["prompt"]}]
    if not 1 <= args.turn <= len(turns):
        raise ValueError("Turn is outside the task's turn range")
    if prompt_path.is_relative_to(workspace) or prompt_path.exists():
        raise ValueError("Choose a new prompt file outside the candidate workspace")
    issue = None
    if "fixture" in task:
        if not args.official_issue:
            raise ValueError("Repository tasks require the pinned official problem statement")
        checkout = subprocess.run(["git", "rev-parse", "--show-toplevel", "HEAD"], cwd=workspace,
                                  check=True, text=True, capture_output=True, timeout=20).stdout.splitlines()
        if len(checkout) != 2 or Path(checkout[0]).resolve() != workspace or checkout[1] != task["fixture"]["base_commit"]:
            raise ValueError("The repository workspace must be the pinned checkout root")
        ready = subprocess.run(["git", "status", "--porcelain"], cwd=workspace, check=True,
                               text=True, capture_output=True, timeout=20)
        if ready.stdout:
            raise ValueError("Start repository attempts from a clean checkout")
        issue = args.official_issue.read_text(encoding="utf-8").rstrip("\n") + "\n"
    elif args.turn == 1:
        workspace.mkdir(parents=True, exist_ok=True)
        if not workspace.is_dir() or any(workspace.iterdir()):
            raise ValueError("Start the first turn in a fresh workspace")
    elif not workspace.is_dir():
        raise ValueError("Later turns use the original attempt workspace")

    turn = turns[args.turn-1]
    if args.turn == 1:
        write_fixtures(workspace, task.get("initial_files", {}), args.seed)
    write_fixtures(workspace, turn.get("add_files", {}), args.seed)
    prompt = turn["turn"].replace("<SEED>", str(args.seed))
    if not task.get("dialogue"):
        prompt = PROMPT_HEADER + prompt
    if issue is not None:
        prompt += "\n\n官方问题\n" + issue
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    with prompt_path.open("x", encoding="utf-8", newline="\n") as file:
        file.write(prompt)
    return {"task_id": task["id"], "seed": args.seed, "turn": args.turn, "turns": len(turns),
            "deadline_seconds_for_entire_attempt": min(task["deadline_seconds"], cap)}


def score(suite, rules, grade_rows, seeds):
    if not isinstance(grade_rows, list):
        raise ValueError("Expected a JSON array of independent grades")
    awards = {}
    for row in grade_rows:
        ident, seed = row["task_id"], row["seed"]
        if ident not in rules or type(seed) is not int or seed not in seeds or (ident, seed) in awards:
            raise ValueError(f"Unknown or duplicate trial {ident}/{seed}")
        maximum = {item["id"]: item["points"] for item in rules[ident]["criteria"]}
        criteria = {item["criterion_id"]: item for item in row["criteria"]}
        if criteria.keys() != maximum.keys() or len(criteria) != len(row["criteria"]):
            raise ValueError(f"Criterion IDs differ for {ident}/{seed}")
        points = []
        for code, limit in maximum.items():
            award = criteria[code]["points_awarded"]
            if criteria[code]["points_possible"] != limit or (award is not None and not valid_score(award, limit)):
                raise ValueError(f"Invalid award for {ident}/{seed}/{code}")
            points.append(award)
        total = None if None in points else sum(points)
        if row["task_score"] != total:
            raise ValueError(f"Grade total differs for {ident}/{seed}")
        awards[ident, seed] = total

    dimensions = []
    for dim in suite["dimensions"]:
        tasks = []
        for task in dim["tasks"]:
            ident = task["id"]
            points = [awards.get((ident, seed)) for seed in seeds]
            tasks.append({"id": ident, "scores": points,
                          "score": None if None in points else statistics.mean(points)})
        values = [task["score"] for task in tasks]
        dimensions.append({"name": dim["name"], "score": None if None in values else sum(values), "tasks": tasks})
    values = [dim["score"] for dim in dimensions]
    return {"seeds": seeds, "dimensions": dimensions, "complete_dimensions": sum(x is not None for x in values),
            "total": None if None in values else round(sum(values), 1),
            "mean": None if None in values else statistics.mean(values), "maximum_total": 100}


def valid_score(value, maximum):
    return type(value) in (int, float) and 0 <= value <= maximum and value * 2 % 1 == 0


def verify(suite, rubric, result):
    version = result["suite_version"]
    if type(version) is not int or version < 1:
        raise ValueError("Invalid result suite version")
    tasks_path, rubric_path = TASKS, RUBRIC
    if version != suite["version"]:
        archive = TASKS.parent / "archive" / f"v{version}"
        tasks_path, rubric_path = archive / "tasks.json", archive / "rubric.json"
        if not (tasks_path.is_file() and rubric_path.is_file()):
            raise ValueError(f"No archived manifests for suite version {version}")
        suite, rubric = read(tasks_path), read(rubric_path)
        index(suite, rubric)
    for field, path in (("tasks_sha256", tasks_path), ("rubric_sha256", rubric_path)):
        if result[field] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f"File digest differs: {path.name}")
    if (suite["version"] != rubric["suite_version"] or suite["version"] != version
            or suite["maximum_score"] != 100 or result["maximum_total"] != 100):
        raise ValueError("Version or scale differs")
    rows = result["dimensions"]
    if [d["name"] for d in rows] != [d["name"] for d in suite["dimensions"]]:
        raise ValueError("Result dimensions differ")
    for dim, expected in zip(rows, suite["dimensions"]):
        if [t["id"] for t in dim["tasks"]] != [t["id"] for t in expected["tasks"]]:
            raise ValueError(f"Result task IDs differ for {dim['name']}")
        for task, spec in zip(dim["tasks"], expected["tasks"]):
            if task["max_points"] != spec["max_points"] or not valid_score(task["score"], spec["max_points"]):
                raise ValueError(f"Out-of-range score for {task['id']}")
        if dim["max_points"] != 10 or dim["score"] != sum(t["score"] for t in dim["tasks"]):
            raise ValueError(f"Dimension sum differs for {dim['name']}")
    totals = [d["score"] for d in rows]
    if result["total"] != sum(totals) or result["mean"] != statistics.mean(totals):
        raise ValueError("Overall total or mean differs")
    return {"suite_version": suite["version"], "questions": sum(len(d["tasks"]) for d in rows),
            "total": result["total"], "mean": result["mean"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    confirm = sub.add_parser("verify", help="check the active suite and verify a result against its version")
    confirm.add_argument("--result", type=Path, default=RESULT)
    setup = sub.add_parser("prepare", help="materialize one turn and its prompt")
    setup.add_argument("task_id")
    setup.add_argument("--workspace", type=Path, required=True)
    setup.add_argument("--prompt-out", type=Path, required=True)
    setup.add_argument("--turn", type=int, default=1)
    setup.add_argument("--seed", type=int, default=7291)
    setup.add_argument("--official-issue", type=Path)
    grading = sub.add_parser("score", help="aggregate one model's independent grade records")
    grading.add_argument("grades", type=Path)
    grading.add_argument("--seed", action="append", type=int)
    args = parser.parse_args()
    try:
        suite, rubric = read(TASKS), read(RUBRIC)
        tasks, rules = index(suite, rubric)
        if args.command == "verify":
            result = verify(suite, rubric, read(args.result))
        elif args.command == "prepare":
            if args.task_id not in tasks:
                raise ValueError(f"Unknown task {args.task_id}")
            result = prepare(tasks[args.task_id], args, suite["execution"]["deadline_cap_seconds_per_case"])
        else:
            seeds = args.seed or [7291]
            if len(set(seeds)) != len(seeds):
                raise ValueError("Seeds must be distinct")
            result = score(suite, rules, read(args.grades), seeds)
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
