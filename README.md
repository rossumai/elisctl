# How to use

Install the package:
```shell
pip install -e .
```

Run something like:
```shell
elisctl transform_schema default_schema.json substitute-options --id centre <( \
   elisctl xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 --sheet 1 | elisctl csv_to_options - ) \
 | elisctl transform_schema - substitute-options --id gl_code <( \
    elisctl xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 | elisctl csv_to_options - ) \
 | elisctl transform_schema - remove contract \
 > era_schema.json
```
