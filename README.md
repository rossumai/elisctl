# How to use

Install the package:
```shell
pip install -e .
```

Run something like:
```shell
transform_schema default_schema.json substitute-options --id centre <( \
    xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 --sheet 1 | csv_to_options - ) \
 | transform_schema - substitute-options --id gl_code <( \
    xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 | csv_to_options - ) \
 | transform_schema - remove contract \
 > era_schema.json
```
