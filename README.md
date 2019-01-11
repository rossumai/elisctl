# How to use

Install the package:
```shell
pip install -e .
```

Run something like:
```shell
elisctl schema transform default_schema.json substitute-options centre <( \
   elisctl tools xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 --sheet 1 | elisctl tools csv_to_options - ) \
 | elisctl schema transform - substitute-options gl_code <( \
    elisctl tools xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 | elisctl tools csv_to_options - ) \
 | elisctl schema transform - remove contract \
 > era_schema.json
```
