# How to use

```shell
tools/xls_to_csv.py ~/Downloads/ERA_osnova_strediska.xlsx --header 0 --sheet 1 \
 | tools/csv_to_options.py - \
 | tools/transform_schema.py <( \
 xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 \
   | tools/csv_to_options.py - \
   | tools/transform_schema.py default_schema.json substitute-options --id gl_code - \
   | tools/transform_schema.py - remove contract \
 ) substitute-options --id centre - > era_schema.json
```
