"""
Программа для объединения файлов equips1.json и equips2.json в equips.json
Удаляет дубликаты по полю eq_name
"""
import json
import logging
from pathlib import Path
from typing import Callable, Optional


def load_json_file(
    file_path: Path,
    logger: Optional[Callable[[str], None]] = None
) -> list[dict]:
    """
    Загружает JSON файл и возвращает список equips.
    
    Args:
        file_path: Путь к JSON файлу
        logger: Опциональная функция для логирования (по умолчанию print)
    
    Returns:
        Список словарей с данными оборудования
    
    Raises:
        FileNotFoundError: Если файл не найден
        JSONDecodeError: Если файл содержит некорректный JSON
        PermissionError: Нет доступа к файлу
        ValueError: Если данные не содержат ключ 'equips'
    """
    _log = logger if logger is not None else print
    
    # Normalize Path object
    path = Path(file_path)
    
    # Validate file exists before attempting to open
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    
    if not path.is_file():
        raise ValueError(f"Ожидался файл, получено: {path}")
    
    # Handle empty files
    if path.stat().st_size == 0:
        _log(f"ПРЕДУПРЕЖДЕНИЕ: Файл {path.name} пуст, возвращен пустой список")
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Некорректный JSON в файле {path.name}: {e.msg}",
            e.doc,
            e.pos
        ) from e
    
    # Validate expected data structure
    if not isinstance(data, dict):
        raise ValueError(
            f"Ожидался словарь в корне JSON, получен {type(data).__name__}"
        )
    
    if 'equips' not in data:
        _log(
            f"ПРЕДУПРЕЖДЕНИЕ: Ключ 'equips' не найден в {path.name}, "
            "возвращен пустой список"
        )
        return []
    
    equips = data['equips']
    
    # Validate equips is a list
    if not isinstance(equips, list):
        raise ValueError(
            f"Ожидался список для 'equips', получен {type(equips).__name__}"
        )
    
    _log(f"Загружено {len(equips)} записей из {path.name}")
    return equips


def load_json_file_safe(
    file_path: Path,
    logger: Optional[Callable[[str], None]] = None
) -> list[dict]:
    """
    Безопасная версия load_json_file с обработкой всех исключений.
    Возвращает пустой список при любой ошибке.
    
    Args:
        file_path: Путь к JSON файлу
        logger: Опциональная функция для логирования
    
    Returns:
        Список словарей с данными оборудования (пустой список при ошибке)
    """
    _log = logger if logger is not None else print
    
    try:
        return load_json_file(file_path, logger=_log)
    except FileNotFoundError as e:
        _log(f"ПРЕДУПРЕЖДЕНИЕ: {e}")
        return []
    except (json.JSONDecodeError, ValueError) as e:
        _log(f"ОШИБКА валидации {Path(file_path).name}: {e}")
        return []
    except PermissionError as e:
        _log(f"ОШИБКА: Нет доступа к файлу {Path(file_path).name}: {e}")
        return []
    except Exception as e:
        _log(f"ОШИБКА при чтении {Path(file_path).name}: {e}")
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
    
    # Загружаем файлы (load_json_file_safe для устойчивости, load_json_file для детальных ошибок)
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
