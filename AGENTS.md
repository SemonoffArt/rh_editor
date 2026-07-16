# AGENTS.md

## Project
Single-file Tkinter app (`mh_editor.py`) that reads/writes Siemens S7 PLC maintenance-hour counters (DINT values) via `python-snap7`. UI labels/logs are in Russian.

## Commands

```bash
.venv\Scripts\Activate.ps1    # activate venv (Windows PS)
python mh_editor.py            # run the app
pip install -r requirements.txt  # deps: only python-snap7==2.0.2
```

Build standalone exe:
```bash
pyinstaller --onefile --windowed --icon=resources/icon.ico ^
  --add-data "equips.json;." --add-data "plc.json;." ^
  --add-data "resources;resources" ^
  --add-binary ".venv\Lib\site-packages\snap7\lib\snap7.dll;snap7\lib" ^
  mh_editor.py
```

## Structure

| Path | Purpose |
|---|---|
| `mh_editor.py` | Single entry point, `MHEditor(tk.Tk)` class |
| `equips.json` | Equipment-to-PLC DB mapping (`eq_name`, `plc_name`, `db_num`, `db_addr`) |
| `plc.json` | PLC connection params (`plc_addr`, `rack`, `slot`, `zif`) |
| `utils/` | Tag converters (ECS7 MDB/SQLite, ECS8, WinCC) + `merge_equips.py` |
| `output/` | Pre-built `mh_editor.exe` |

## Key facts

- **No tests, no CI, no linter/formatter/typecheck config** — run manually only
- **Config JSON encoding**: UTF-8, keys `"equips"` / `"plc"` wrapping arrays
- **Hours limit**: 50 000 (`MAX_HOURS` constant in `mh_editor.py:15`)
- **PLC data format**: DINT (4 bytes), read via `snap7.util.get_dint/set_dint`
- **Converter convention**: DB address = `offset + 16` for ECS converters
- **`resource_path()`** (`mh_editor.py:17-23`): resolves paths for both dev and PyInstaller (`sys._MEIPASS`)
- `utils/exceptions.py` is **unrelated** (imported by ECS MDB tool but not by the main app)
- Useful utils: `python utils/merge_equips.py` merges `utils/equips1.json` + `utils/equips2.json` → `utils/equips.json` (de-duplicates by `eq_name`)
