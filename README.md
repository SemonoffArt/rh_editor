# rh_editor

Утилита для корректировки часов обслуживания оборудования через Siemens PLC (S7) с помощью snap7 и графического интерфейса на Tkinter.

## Возможности

- Просмотр и фильтрация списка оборудования по тегу и ЗИФ.
- Чтение и запись значения часов обслуживания (в секундах и часах) в ПЛК Siemens через DB-адреса.
- Работа с несколькими ПЛК, поддержка конфигурации через JSON-файлы.
- Ведение лога действий.
- Удобный графический интерфейс на Python (Tkinter).
- Поддержка выбора ЗИФ и поиска по тегу.
- Встроенная справка.

## Установка

1. Клонируйте репозиторий:
   ```sh
   git clone https://github.com/yourusername/rh_editor.git
   cd rh_editor
   ```

2. Установите зависимости:
   ```sh
   pip install -r requirements.txt
   ```

3. Убедитесь, что у вас есть файлы конфигурации:
   - `equips.json` — список оборудования и адреса DB.
   - `plc.json` — параметры подключения к ПЛК (IP, rack, slot, zif).

4. (Опционально) Проверьте наличие файла иконки: `resources/icon.ico`.

## Запуск

```sh
python mh_editor.py
```

## Формат файлов конфигурации

### plc.json

```json
{
  "plc": [
    {
      "plc_name": "PLC1",
      "plc_addr": "192.168.0.1",
      "rack": 0,
      "slot": 1,
      "zif": 1
    }
    // ...
  ]
}
```

### equips.json

```json
{
  "equips": [
    {
      "eq_name": "Tag1",
      "plc_name": "PLC1",
      "db_num": 1,
      "db_addr": 100
    }
    // ...
  ]
}
```

## Зависимости

- Python 3.7+
- snap7
- tkinter (обычно входит в стандартную библиотеку Python)
- ttk (часть tkinter)

## Автор

- semonoff@gmail.com
- 7Art, 2025
