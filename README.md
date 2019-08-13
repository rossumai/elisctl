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
interactively or programmatically.

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
## Configure profiles

To run commands described below under a chosen user, it is possible to use profiles defined by
configure function such as
```shell
elisctl --profile profile_name configure
```

After defining necessary profiles and their credentials, the profile can be chosen the following way
```shell
elisctl --profile profile_name queue list
```

## Edit Schema

Some of the most common advanced operations are related to setting up
the sidebar-describing schema according to business requirements. Using elisctl
you can edit schema easily as a JSON file.

List queues to obtain schema id:
```shell
elisctl queue list
  id  name                           workspace  inbox                                       schema  users
----  ---------------------------  -----------  ----------------------------------------  --------  ----------------------
   6  My Queue 1                             6  myqueue-ab12ee@elis.rossum.ai                    7  27
```

Download schema as a json:
```shell
elisctl schema get 7 -O schema.json
```

Open `schema.json` file in you favourite editor and upload modified version back to Elis.
```shell
elisctl schema update 7 schema.json
```

From now on, documents will follow new schema.

As an experimental feature, you can also edit schema as an Excel (xlsx) file.
```shell
elisctl schema get 7 --format xlsx -O schema.xlsx
elisctl schema update 7 schema.xlsx
```


## Schema Transformations

In addition, there is a scripting support for many common schema operations,
that may be easily used for schema management automation. See `elisctl schema transform`
and `elisctl tools` tools for further reference.

Run something like:
```shell
elisctl schema transform substitute-options default_schema.json centre <( \
   elisctl tools xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 --sheet 1 | elisctl tools csv_to_options - ) \
 | elisctl schema transform substitute-options - gl_code <( \
    elisctl tools xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 | elisctl tools csv_to_options - ) \
 | elisctl schema transform remove - contract \
 > era_schema.json
```

## License
MIT

## Contributing

* Submit a pull request from forked version of this repo. 
And select any of the maintainers as a reviewer.
* Use [`pre-commit`](https://pre-commit.com/#install) to avoid linting issues.
* When releasing, a `Collaborator` with `Admin` role shall run in `master` branch:
    ```bash
    bump2version minor
    git push
    git push --tags
    ``` 
 * To build a Windows installer, run:
     ```bash
    pynsist installer.cfg
    ``` 
   
## Changelog

### 2019-07-30 v2.6.0
* Enable passing custom filename with upload

### 2019-07-12 v2.5.0

* Add support for schema specified in XLSX when creating queue
* Remove the necessity to specify schema file type when uploading
* Fix XML and CSV formats of `elisctl document extract`

### 2019-07-09 v2.4.0

* Add support for can_export in xlsx schema format
* Add document command

### 2019-06-21 v2.3.1

* Fix: annotator cannot use `elisctl connector list` command

### 2019-06-13 v2.3.0

* Add connector command

### 2019-06-11 v2.2.1

* Update packages for windows build.


### 2019-06-03 v2.2.0

* Added support for [`--profile`](#configure-profiles) option to all `elisctl` commands
* Fix: remove extra whitespace in xlsx schema export/import

### 2019-04-02 v2.1.0

* Added support for `--output-file` to `elisctl tools` and `elisctl schema transform`
* Fix [Schema Transformations](#schema-transformations) description in README

### 2019-03-14 v2.0.1

* Fixed MS Windows application entry point (running elisctl from the start menu)
* Fixed parsing of boolean values in xlsx schema export/import

### 2019-03-14 v2.0.0

* Disable interpolation in config parsing, so that special characters are allowed in e.g. password
* Experimental support for schema modification using xlsx file format
* Allow to show help in schema transform add (backward incompatible change)

### 2019-03-08 v1.1.1

* Fixed bug with UnicodeDecodeError in `elisctl schema get ID -O file.json` on Windows

### 2019-03-03 v1.1.0

* Added support for python 3.6
* Added `User-Agent` header (`elisctl/{version} ({platform})`) for every request to ELIS API
* Improved error when login fails with the provided credentials
