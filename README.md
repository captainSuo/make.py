# make.py

A lightweight, zero-dependency build system in pure Python.

## Quick Start

Copy `make.py` to your working directory, and place your build logic below the `BUILD CODE HERE` marker.

```python
# Build a target from a dependency
@target("build/app")
@depend("src/main.c", "src/utils.c")
def build_app():
    run("mkdir -p build", silent=True)
    run("gcc src/main.c src/utils.c -o build/app")

# Define a phony task (always runs)
@task
def clean():
    run("rm -rf build")
```

## Terminal Commands

Execute your tasks from the command line:

```bash
# Build a specific target
$ python make.py build/app

# Run a phony task
$ python make.py clean
```

## API Reference

*   `@target(name)`: Marks a function as a file-producing task.
*   `@depend(*deps)`: Declares file dependencies for a task.
*   `@task`: Marks a function as a phony task (runs every time).
*   `run(cmd, silent=False)`: Executes a shell command and exits on failure.
