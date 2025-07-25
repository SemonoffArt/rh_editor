import pandas as pd
import json
import re
import sys
import os


def main():
    try:
        # Укажите путь к файлу
        file_path = os.path.join('resources', 'Points.xlsx')
        if not os.path.exists(file_path):
            print(f"Файл не найден: {file_path}")
            sys.exit(1)

        # Загружаем Excel-файл в DataFrame
        df = pd.read_excel(file_path)

        # Фильтруем строки, где в столбце 'Designation' содержится 'maint_mh'
        filter_regex = r'.+maint.+mh(_\d+)?$'
        df_filtered = df[df['Designation'].str.contains(filter_regex, flags=re.IGNORECASE, regex=True)]

        # Формируем список словарей для equips2.json
        result = []
        for _, row in df_filtered.iterrows():
            try:
                equip = {
                    "eq_name": row.get("Designation", ""),
                    "plc_name": str(row.get("IOType_0", ""))[0:3],
                    "db_num": int(row.get("IOType_2", None)),
                    "db_addr": int(row.get("IOType_3", None)) + 16
                }
                result.append(equip)
            except Exception as e:
                print(f"Ошибка обработки строки: {e}")
                continue

        # Сохраняем в equips2.json
        output_path = "equips2.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"equips": result}, f, ensure_ascii=False, indent=4)

        print(f"Сохранено {len(result)} записей в {output_path}")
        input("Нажмите Enter для выхода...")
    except ImportError as e:
        print(f"Ошибка импорта: {e}\nУбедитесь, что установлены все необходимые библиотеки: pandas, openpyxl")
        input("Нажмите Enter для выхода...")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        input("Нажмите Enter для выхода...")


if __name__ == '__main__':
    main()
