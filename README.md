# AVR-Python-Libraries

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Install

To install the base package, run:

```bash
pip install bell-avr-libraries
```

Additionally, the `serial` and `qt` extras are available if you want to use
the PCC or PySide functionality.

```bash
pip install bell-avr-libraries[serial,qt]
```

## Usage

See the documentation website at [https://bellflight.github.io/AVR-Python-Libraries](https://bellflight.github.io/AVR-Python-Libraries)

## Development

It's assumed you have a version of Python installed from
[python.org](https://python.org) that is the same or newer as
defined in the [`.python-version`](.python-version) file.

First, install [Poetry](https://python-poetry.org/) and
[VS Code Task Runner](https://pypi.org/project/vscode-task-runner/):

```bash
python -m pip install pipx --upgrade
pipx ensurepath
pipx install poetry
pipx install vscode-task-runner
# (Optionally) Add pre-commit plugin
poetry self add poetry-pre-commit-plugin
```

Now, you can clone the repo and install dependencies:

```bash
git clone https://github.com/bellflight/AVR-Python-Libraries
cd AVR-Python-Libraries
vtr install
```

Run

```bash
poetry shell
```

to activate the virtual environment.

You can now produce a package with `vtr build`, which will automatically
also run `vtr build-code`.

To add new message definitions, add entries to the `bell/avr/mqtt/asyncapi.yml` file.
This is an [AsyncAPI](https://www.asyncapi.com/) definition,
which is primarily [JSONSchema](https://json-schema.org/) with some association
of classes and topics.

The generator that turns this definition file into Python code is the homebrew
[build.py](build.py), so double-check that the output makes sense.

To generate the documentation, `vtr build-code-docs`.
This requires that Node.js is installed.
