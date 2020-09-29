# elisctl


:exclamation: This library is deprecated.
Use [rossum](https://pypi.org/project/rossum/) library instead :exclamation:


## Changelog

### 2020-07-27 v2.10.1
* Fix attribute name for setting max token lifetime

### 2020-07-24 v2.10.0
* Add `schema list` command
* Fix `webhook change` command issue
* Remove `csv get` command
* Add example script for setting up a new organisation
* Enable assigning manager role to user
* Enable setting max token lifetime
* Catch ValueError when parsing schema in XLSX
* Fix Python3.8 support

### 2020-02-18 v2.9.0
* allow editing inbox attributes separately on queue-related commands
* add support for `can_collapse` in xlsx schema
* add sample usage of elisctl library in a Python code
* make queue option required on `user create`

### 2019-10-31 v2.8.0
* Add webhook command
* Allow creating and changing inbox properties on `queue change` command

### 2019-09-30 v2.7.1
* Improve documentation

### 2019-08-13 v2.7.0
* Add command `user_assignment` for bulk assignment of users to queues
* Change command `connector create`: `queue_id` parameter needs to be specified, if there is more than one queue in organization
* Support schema attribute `width` in XLSX schema format
* Fixed: booleans, in XLSX schema format, can be specified as boolean types
* Internal: filename can be specified in `ELISClient.upload_document`


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
* Added `User-Agent` header (`elisctl/{version} ({platform})`) for every request to ROSSUM API
* Improved error when login fails with the provided credentials
