"""
Copyright (c) 2026 captainSuo

make.py - A lightweight, zero-dependency build system in pure Python.

Example usage (place your code below the "BUILD CODE HERE" marker):

> @target("build/app")
> @depend("src/main.c")
> def build_app():
>     run("mkdir -p build", silent=True)
>     run("gcc src/main.c -o build/app")
>
> @task
> def clean():
>     run("rm -rf build")

Terminal commands:
    $ python make.py            # Builds the first target
    $ python make.py build/app  # Builds the specified target
    $ python make.py clean      # Runs the clean task
"""

import os
import sys
import subprocess
import concurrent.futures
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import NoReturn, TypeAlias
from pathlib import Path

TaskFunc: TypeAlias = Callable[[], None]
TASKS: dict[str, 'Task'] = {}


@dataclass
class Task:
    func: TaskFunc
    name: str
    deps: tuple[str, ...]
    phony: bool

    def __call__(self):
        return self.func()

    @property
    def __name__(self):
        return self.name


def die(msg: str) -> NoReturn:
    print(f"\033[1;91merror:\033[0m {msg}")
    sys.exit(1)


def run(cmd: str, silent: bool = False) -> None:
    if not silent: print(cmd)
    if subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL if silent else None).returncode != 0:
        die(f"command failed: {cmd}")


def task(func: Callable, phony: bool = True) -> Task:
    return TASKS.setdefault(func.__name__, Task(func, func.__name__, getattr(func, "deps", ()), phony))


def depend(*deps: str) -> Callable[[TaskFunc], TaskFunc]:
    return lambda func: setattr(func, "deps", deps) or func


def target(name: str) -> Callable[[TaskFunc], TaskFunc]:
    return lambda func: task(setattr(func, "__name__", name) or func, False)


def gather(futures: Iterable[concurrent.futures.Future]):
    return [f.result() for f in futures]


def build(task_name: str) -> None:
    if task_name not in TASKS:
        die(f"no task named {task_name!r}")

    tasks_to_run: list[Task] = []
    names_visited: set[str]  = set()
    names_dirty:   set[str]  = set()

    def get_mtime(dep: str) -> float:
        if dep in names_dirty:
            return float('inf')
        return Path(dep).stat().st_mtime

    def resolve(name: str) -> None:
        if name in names_visited: return
        names_visited.add(name)

        if not (t := TASKS.get(name)):
            if not Path(name).exists():
                die(f"missing dependency: {name}")
            return

        for dep in t.deps:
            resolve(dep)

        max_mtime = max((get_mtime(d) for d in t.deps), default=0.0)

        if t.phony:
            tasks_to_run.append(t)
            names_dirty.add(t.name)
        else:
            t_path = Path(t.name)
            if not t_path.exists() or t_path.stat().st_mtime < max_mtime:
                tasks_to_run.append(t)
                names_dirty.add(t.name)

    resolve(task_name)
    if not tasks_to_run:
        return print(f"\033[1;93mskip:\033[0m {task_name} is up to date")

    futures_by_name: dict[str, concurrent.futures.Future] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        for t in tasks_to_run:
            dep_futures = [futures_by_name[d] for d in t.deps if d in futures_by_name]

            def run_task(task_obj: Task, deps_f: list[concurrent.futures.Future]):
                gather(deps_f)
                prefix = "\033[1;92mtarget:\033[0m" if task_obj.phony else "\033[1;92mbuild:\033[0m"
                print(f"{prefix} {task_obj.name}")
                task_obj()
                if not task_obj.phony:
                    Path(task_obj.name).touch()

            futures_by_name[t.name] = executor.submit(run_task, t, dep_futures)

        gather(futures_by_name.values())


def main():
    try:
        build(sys.argv[1])
    except IndexError:
        if TASKS:
            build(next(iter(TASKS)))
        else:
            die("no targets defined")
    except SystemExit as e:
        sys.stdout.flush()
        os._exit(int(e.code or 0))
    except Exception as e:
        print(f"\033[1;91merror:\033[0m {e}")
        sys.stdout.flush()
        os._exit(1)


# =========================================================
#                  BUILD CODE BELOW
# =========================================================

# Place your task definations here.

if __name__ == "__main__":
    main()  # entry point of make.py
