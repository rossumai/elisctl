# elisctl

[![PyPI - version](https://img.shields.io/pypi/v/elisctl.svg)](https://pypi.python.org/pypi/elisctl)
[![Build Status](https://travis-ci.com/rossumai/elisctl.svg?branch=master)](https://travis-ci.com/rossumai/elisctl)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![codecov](https://codecov.io/gh/rossumai/elisctl/branch/master/graph/badge.svg)](https://codecov.io/gh/rossumai/elisctl)
![PyPI - supported python versions](https://img.shields.io/pypi/pyversions/elisctl.svg)
![MIT licence](https://img.shields.io/pypi/l/elisctl.svg)

**elisctl** is a set of tools that wrap
the [Elis Document Management API](https://api.elis.rossum.ai/docs)
to provide an easy way to configure, integrate and customize Elis - either
interactively or programmaticaly.

## Installation

### Windows

Download an installation file from
[GitHub releases](https://github.com/rossumai/elisctl/releases).
Install it. And run it either from start menu or from command prompt.


### UNIX based systems

Install the package from PyPI:
```bash
pip install elisctl
```

## How to use

Individual Elis operation are triggered by passing specific *commands* to `elisctl`.
Commands are organized by object type in a tree-like structure and thus are composed
of multiple words (e.g. `user create` or `schema transform`).

The **elisctl** tool can be either used in a **command line interface** mode
by executing each command through `elisctl` individually by passing it as an argument,
or in an **interactive shell** mode of executing `elisctl` without parameters
and then typing the commands into the shown prompt.

So either get the list of commands and execute them immediately such as:
```shell
elisctl --help
elisctl configure
```
or run the interactive shell by simply running
```shell
elisctl
```

## Schema Transformations

Some of the most common advanced operations are related to setting up
the sidebar-describing schema JSON according to business requirements
and enumerations.
`elisctl schema transform` and `elisctl tools` are designed to help
with these operations.

Run something like:
```shell
elisctl schema transform default_schema.json substitute-options centre <( \
   elisctl tools xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 --sheet 1 | elisctl tools csv_to_options - ) \
 | elisctl schema transform - substitute-options gl_code <( \
    elisctl tools xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 | elisctl tools csv_to_options - ) \
 | elisctl schema transform - remove contract \
 > era_schema.json
```

## License
MIT

## Contributing

* Submit a pull request from forked version of this repo. 
And select any of the maintainers as a reviewer.
* Use [`pre-commit`](https://pre-commit.com/#install) to avoid linting issues.
* When releasing, run in `master` branch:
    ```bash
    bumpversion minor
    git push
    git push --tags
    ``` 
 
## Changelog

### 2019-03-03 v1.1.0

* Added support for python 3.6
* Added `User-Agent` header (`elisctl/{version} ({platform})`) for every request to ELIS API
* Improved error when login fails with the provided credentials
