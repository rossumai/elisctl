# How to use

```shell
./xls_to_csv.py ~/Downloads/WASSA_osnova.xlsx --header 0 --sheet 0 | ./csv_to_options.py - | ./options_to_schema.py --id gl_code --schema ../schema.json - > ../schema2.json
```
