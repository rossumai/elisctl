# How to use

```shell
./xls_to_csv.py ~/Downloads/WASSA_osnova.xlsx --header 0 --sheet 0 | ./csv_to_options.py - | ./transform_schema.py ../schema.json substitute-options --id gl_code - | ./transform_schema.py - remove centre > ../schema2.json
```
