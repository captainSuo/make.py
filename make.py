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
import atexit
from collections.abc import Callable
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
    print(f"error: {msg}")
    sys.exit(1)


def run(cmd: str, silent: bool = False) -> None:
    if not silent: print(cmd)
    if subprocess.run(cmd, shell=True).returncode != 0:
        die(f"command failed: {cmd}")


def task(func: Callable, phony: bool = True) -> Task:
    return TASKS.setdefault(func.__name__, Task(func, func.__name__, getattr(func, "deps", ()), phony))


def depend(*deps: str) -> Callable[[TaskFunc], TaskFunc]:
    return lambda func: setattr(func, "deps", deps) or func


def target(name: str) -> Callable[[TaskFunc], TaskFunc]:
    return lambda func: task(setattr(func, "__name__", name) or func, False)


def fetch_dep_mtime(dep: str, visited: set[str]) -> float:
    if dep in TASKS:
        build(dep, visited)

    if not (p := Path(dep)).exists():
        die(f"missing dep: {dep}")
    return p.stat().st_mtime


def build(name: str, visited: set[str] | None = None) -> None:
    if name in (visited := visited or set()): return
    visited.add(name)

    if not (t := TASKS.get(name)):
        die(f"unknown target: {name}")

    max_mtime = max((fetch_dep_mtime(d, visited) for d in t.deps), default=0.0)

    if t.phony:
        print(f"\033[93mbuild:\033[0m {t.name}")
        return t()

    t_path = Path(t.name)
    if t_path.exists() and t_path.stat().st_mtime >= max_mtime:
        return print(f"\033[92mskip:\033[0m {t.name} is up to date")

    print(f"\033[93mbuild:\033[0m {t.name}")
    t()
    t_path.touch()


if __name__ == "__main__":
    @atexit.register
    def _main():
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




# =========================================================
#           BUILD CODE HERE
# =========================================================
