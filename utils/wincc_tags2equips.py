#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сравнения equips.json с mh_wincc_tags.xlsx
и создания equips_wincc.json с отсутствующими тегами
"""
import pandas as pd
import json
import re
import sys
import os
from pathlib import Path


def extract_db_info(address):
    """
    Извлекает номер DB и адрес из строки Address
    Например: "%DB6068.DBD2" -> db_num=6068, db_addr=18 (2+16)
    """
    try:
        # Паттерн для извлечения: %DB<номер>.DBD<адрес>
        pattern = r'%DB(\d+)\.DBD(\d+)'
        match = re.search(pattern, address)
        
        if match:
            db_num = int(match.group(1))
            db_offset = int(match.group(2))
            db_addr = db_offset + 16
            return db_num, db_addr
        else:
            print(f"Предупреждение: Не удалось распарсить адрес '{address}'")
            return None, None
    except Exception as e:
        print(f"Ошибка при обработке адреса '{address}': {e}")
        return None, None


def load_equips_json(file_path):
    """Загружает equips.json и возвращает словарь с eq_name в качестве ключей"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            equips_dict = {eq['eq_name']: eq for eq in data.get('equips', [])}
            print(f"Загружено {len(equips_dict)} записей из equips.json")
            return equips_dict
    except FileNotFoundError:
        print(f"ОШИБКА: Файл {file_path} не найден!")
        return {}
    except Exception as e:
        print(f"ОШИБКА при чтении equips.json: {e}")
        return {}


def load_wincc_tags(file_path):
    """Загружает mh_wincc_tags.xlsx и возвращает DataFrame"""
    try:
        df = pd.read_excel(file_path)
        print(f"Загружено {len(df)} записей из mh_wincc_tags.xlsx")
        print(f"Столбцы в файле: {', '.join(df.columns.tolist())}")
        return df
    except FileNotFoundError:
        print(f"ОШИБКА: Файл {file_path} не найден!")
        return None
    except Exception as e:
        print(f"ОШИБКА при чтении mh_wincc_tags.xlsx: {e}")
        return None


def compare_and_create_missing(equips_dict, wincc_df):
    """
    Сравнивает данные и создает список отсутствующих тегов
    """
    if wincc_df is None or wincc_df.empty:
        print("ОШИБКА: WinCC данные пусты")
        return []
    
    missing_equips = []
    skipped_count = 0
    
    for index, row in wincc_df.iterrows():
        try:
            # Получаем имя тега из Tag_ScreenNumber
            tag_name = str(row.get('Name', '')).strip()
            
            if not tag_name or tag_name == 'nan':
                skipped_count += 1
                continue
            
            # Проверяем, содержит ли тег "_MH"
            if '_MH' not in tag_name:
                skipped_count += 1
                continue
            
            # Проверяем, есть ли тег в equips.json
            if tag_name not in equips_dict:
                # Извлекаем Connection (убираем префикс 'PLC_')
                connection = str(row.get('Connection', '')).strip()
                plc_name = connection.replace('PLC_', '') if connection else ''
                
                # Извлекаем Address и парсим DB информацию
                address = str(row.get('Address', '')).strip()
                db_num, db_addr = extract_db_info(address)
                
                # Получаем описание
                description = str(row.get('Comment [en-US]', '')).strip()
                if description == 'nan':
                    description = ''
                
                # Создаем запись только если удалось извлечь DB информацию
                if db_num is not None and db_addr is not None:
                    equip = {
                        "eq_name": tag_name,
                        "plc_name": plc_name,
                        "db_num": db_num,
                        "db_addr": db_addr,
                        "description": description
                    }
                    missing_equips.append(equip)
                else:
                    print(f"Пропущен тег '{tag_name}': не удалось извлечь DB информацию из '{address}'")
                    skipped_count += 1
        
        except Exception as e:
            print(f"Ошибка обработки строки {index}: {e}")
            skipped_count += 1
            continue
    
    print(f"\nНайдено новых тегов: {len(missing_equips)}")
    print(f"Пропущено записей: {skipped_count}")
    return missing_equips


def save_equips_wincc(equips_list, output_path):
    """Сохраняет список отсутствующих тегов в equips_wincc.json"""
    try:
        data = {"equips": equips_list}
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\nУспешно сохранено {len(equips_list)} записей в {output_path}")
        return True
    except Exception as e:
        print(f"ОШИБКА при сохранении equips_wincc.json: {e}")
        return False


def main():
    """Главная функция"""
    print("="*60)
    print("WinCC Tags to Equips - Поиск отсутствующих тегов")
    print("="*60)
    print()
    
    # Определяем пути к файлам
    script_dir = Path(__file__).parent.absolute()
    equips_json_path = script_dir / 'equips.json'
    wincc_xlsx_path = script_dir / 'resources' / 'mh_wincc_tags.xlsx'
    output_json_path = script_dir / 'equips_wincc.json'
    
    print(f"Директория скрипта: {script_dir}")
    print(f"Путь к equips.json: {equips_json_path}")
    print(f"Путь к mh_wincc_tags.xlsx: {wincc_xlsx_path}")
    print(f"Путь к выходному файлу: {output_json_path}")
    print()
    
    # Загружаем equips.json
    print("Шаг 1: Загрузка equips.json...")
    equips_dict = load_equips_json(equips_json_path)
    
    if not equips_dict:
        print("ПРЕДУПРЕЖДЕНИЕ: equips.json пуст или не найден. Все теги из Excel будут считаться новыми.")
    
    # Загружаем mh_wincc_tags.xlsx
    print("\nШаг 2: Загрузка mh_wincc_tags.xlsx...")
    wincc_df = load_wincc_tags(wincc_xlsx_path)
    
    if wincc_df is None:
        print("ОШИБКА: Не удалось загрузить mh_wincc_tags.xlsx")
        input("\nНажмите Enter для выхода...")
        return
    
    # Сравнение и создание списка отсутствующих тегов
    print("\nШаг 3: Сравнение данных и поиск отсутствующих тегов...")
    missing_equips = compare_and_create_missing(equips_dict, wincc_df)
    
    if not missing_equips:
        print("\nВсе теги из mh_wincc_tags.xlsx уже присутствуют в equips.json")
        print("Новых тегов не найдено.")
    else:
        # Сохранение результата
        print("\nШаг 4: Сохранение результата в equips_wincc.json...")
        if save_equips_wincc(missing_equips, output_json_path):
            print("\n✓ Готово!")
            print(f"\nПервые 3 новых тега:")
            for i, eq in enumerate(missing_equips[:3], 1):
                print(f"  {i}. {eq['eq_name']} -> DB{eq['db_num']}.DBD{eq['db_addr']} ({eq['plc_name']})")
    



if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

