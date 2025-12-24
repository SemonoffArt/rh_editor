"""
Программа для объединения файлов equips1.json и equips2.json в equips.json
Удаляет дубликаты по полю eq_name
"""
import json
from pathlib import Path


def load_json_file(file_path):
    """Загружает JSON файл и возвращает список equips"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            equips = data.get('equips', [])
            print(f"Загружено {len(equips)} записей из {file_path.name}")
            return equips
    except FileNotFoundError:
        print(f"ПРЕДУПРЕЖДЕНИЕ: Файл {file_path.name} не найден, пропускаем")
        return []
    except Exception as e:
        print(f"ОШИБКА при чтении {file_path.name}: {e}")
        return []


def merge_equips(equips1, equips2):
    """
    Объединяет два списка equips, удаляя дубликаты по eq_name
    Приоритет отдается записям из equips1
    """
    # Создаем словарь для быстрого поиска по eq_name
    merged_dict = {}
    
    # Добавляем все записи из equips1
    for eq in equips1:
        eq_name = eq.get('eq_name', '')
        if eq_name:
            merged_dict[eq_name] = eq
    
    # Добавляем записи из equips2, которых нет в equips1
    added_count = 0
    duplicate_count = 0
    
    for eq in equips2:
        eq_name = eq.get('eq_name', '')
        if eq_name:
            if eq_name not in merged_dict:
                merged_dict[eq_name] = eq
                added_count += 1
            else:
                duplicate_count += 1
    
    print(f"\nСтатистика объединения:")
    print(f"  Записей из equips1.json: {len(equips1)}")
    print(f"  Записей из equips2.json: {len(equips2)}")
    print(f"  Добавлено новых из equips2.json: {added_count}")
    print(f"  Пропущено дубликатов: {duplicate_count}")
    print(f"  Всего в результате: {len(merged_dict)}")
    
    # Преобразуем словарь обратно в список, сортируем по eq_name
    merged_list = sorted(merged_dict.values(), key=lambda x: x.get('eq_name', ''))
    return merged_list


def save_merged_equips(equips_list, output_path):
    """Сохраняет объединенный список в equips.json"""
    try:
        data = {"equips": equips_list}
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\n✓ Успешно сохранено {len(equips_list)} записей в {output_path.name}")
        return True
    except Exception as e:
        print(f"\nОШИБКА при сохранении {output_path.name}: {e}")
        return False


def main():
    """Главная функция"""
    print("=" * 60)
    print("Объединение equips1.json и equips2.json")
    print("=" * 60)
    print()
    
    # Определяем пути к файлам
    script_dir = Path(__file__).parent.absolute()
    equips1_path = script_dir / 'equips1.json'
    equips2_path = script_dir / 'equips2.json'
    output_path = script_dir / 'equips.json'
    
    print(f"Директория: {script_dir}")
    print(f"Файл 1: {equips1_path.name}")
    print(f"Файл 2: {equips2_path.name}")
    print(f"Результат: {output_path.name}")
    print()
    
    # Загружаем файлы
    print("Шаг 1: Загрузка файлов...")
    equips1 = load_json_file(equips1_path)
    equips2 = load_json_file(equips2_path)
    
    if not equips1 and not equips2:
        print("\nОШИБКА: Оба файла пусты или не найдены!")
        input("\nНажмите Enter для выхода...")
        return
    
    # Объединяем
    print("\nШаг 2: Объединение данных...")
    merged_equips = merge_equips(equips1, equips2)
    
    # Сохраняем
    print("\nШаг 3: Сохранение результата...")
    if save_merged_equips(merged_equips, output_path):
        print("\n" + "=" * 60)
        print("Готово!")
        print("=" * 60)
        
        # Показываем примеры
        if merged_equips:
            print(f"\nПримеры первых 3 записей:")
            for i, eq in enumerate(merged_equips[:3], 1):
                print(f"  {i}. {eq.get('eq_name', 'N/A')} - {eq.get('plc_name', 'N/A')} - DB{eq.get('db_num', 'N/A')}.DBD{eq.get('db_addr', 'N/A')}")
    
    input("\nНажмите Enter для выхода...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
