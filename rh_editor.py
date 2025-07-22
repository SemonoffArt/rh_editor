import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import snap7
from snap7.util import *

EQUIPS_FILE = 'equips.json'
PLC_FILE = 'plc.json'


class RHEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Редактор часов тех обслуживания')
        self.geometry('800x600')
        self.equips: list = []
        self.filtered_equips: list = []
        self.selected_equip = None
        self.plc_configs: list = self.load_plc_configs()  # Загружаем plc.json
        self.selected_zif = None  # выбранный zif
        self.create_widgets()
        self.load_equips()
        self.update_table()

    # --- Работа с файлами конфигурации ---
    def load_plc_configs(self) -> list:
        if not os.path.exists(PLC_FILE):
            self.add_log(f'ОШИБКА: Файл {PLC_FILE} не найден!')
            return []
        with open(PLC_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('plc', [])

    def load_equips(self) -> None:
        if not os.path.exists(EQUIPS_FILE):
            self.add_log(f'ОШИБКА: Файл {EQUIPS_FILE} не найден!')
            self.equips = []
            return
        with open(EQUIPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.equips = data.get('equips', [])
        self.filtered_equips = self.equips.copy()
        self.add_log(f'Загружено {len(self.equips)} записей оборудования')

    # --- UI ---
    def create_widgets(self) -> None:
        # Filter label and entry
        filter_frame = tk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        # --- ZIF DROPDOWN ---
        tk.Label(filter_frame, text='ЗИФ:', font=("Arial", 16)).pack(side=tk.LEFT, padx=(0, 5))
        self.zif_var = tk.StringVar()
        self.zif_var.set('Все')
        zif_values = self.get_zif_values()
        self.zif_menu = ttk.Combobox(filter_frame, textvariable=self.zif_var, values=['Все'] + zif_values, state='readonly', width=6, font=("Arial", 16))
        self.zif_menu.pack(side=tk.LEFT, padx=(0, 10))
        self.zif_menu.bind('<<ComboboxSelected>>', self.on_zif_change)
        # --- END ZIF DROPDOWN ---

        tk.Label(filter_frame, text='Фильтр по Tag:', font=("Arial", 16)).pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add('write', self.on_filter_change)
        filter_entry = tk.Entry(filter_frame, textvariable=self.filter_var, font=("Arial", 16))
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Кнопка с вопросительным знаком в правом верхнем углу
        self.help_button = tk.Button(
            filter_frame, text="?", command=self.show_help,
            height=1, width=3
        )
        self.help_button.pack(side=tk.RIGHT, padx=(0, 18))


        # Table
        columns = ('Tag', 'plc_name', 'db_num', 'db_addr')
        table_frame = tk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
        vsb = tk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        # Bind double-click event
        self.tree.bind('<Double-1>', self.on_double_click)

        # Read button and result label
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.read_button = tk.Button(
            button_frame, text="READ", command=self.read_plc_data,
            font=("Arial", 16, "bold"), height=1, width=6
        )
        self.read_button.pack(side=tk.LEFT)

        # result label and hours ...

        tk.Label(button_frame, text="Сек:", font=("Arial", 16, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.result_var = tk.StringVar()
        self.result_entry = tk.Entry(
            button_frame, textvariable=self.result_var,
            font=("Arial", 20), width=12, justify="center", state="readonly"
        )
        self.result_entry.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(button_frame, text="Часы: ", font=("Arial", 16, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.hours_var = tk.StringVar()
        vcmd = (self.register(self.validate_hours), '%P')
        self.hours_entry = tk.Entry(
            button_frame, textvariable=self.hours_var,
            font=("Arial", 20, "bold"), width=10,
            validate='key', validatecommand=vcmd
        )
        self.hours_entry.pack(side=tk.LEFT, padx=5)

        # Кнопка WRITE теперь после поля часов
        self.write_button = tk.Button(
            button_frame, text="WRITE", command=self.write_plc_data,
            bg="red", fg="white", font=("Arial", 16, "bold"), height=1, width=6
        )
        self.write_button.pack(side=tk.RIGHT, padx=(0, 18))

        # Log area
        log_frame = tk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(log_frame, text="Лог действий:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        # Create text widget with scrollbar
        text_frame = tk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(text_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def add_log(self, message: str) -> None:
        """Add message to log area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)  # Scroll to bottom
        self.log_text.config(state=tk.DISABLED)

    # --- Фильтрация и обновление таблицы ---
    def get_zif_values(self) -> list:
        # Получить уникальные значения zif из plc.json
        zifs = set()
        for plc in self.plc_configs:
            zif = plc.get('zif')
            if zif is not None:
                zifs.add(str(zif))
        return sorted(zifs, key=lambda x: int(x))

    def on_zif_change(self, event=None):
        self.apply_filters()

    def on_filter_change(self, *args):
        self.apply_filters()

    def apply_filters(self) -> None:
        filter_text = self.filter_var.get().strip().lower()
        selected_zif = self.zif_var.get()
        # Фильтруем equips по Tag и zif
        if selected_zif == 'Все':
            equips = self.equips.copy()
        else:
            # Получаем plc_name, у которых zif совпадает
            plc_names = [plc.get('plc_name') for plc in self.plc_configs if str(plc.get('zif')) == selected_zif]
            equips = [eq for eq in self.equips if eq.get('plc_name') in plc_names]
        if filter_text:
            equips = [eq for eq in equips if filter_text in str(eq.get('eq_name', '')).lower()]
        self.filtered_equips = equips
        self.update_table()

    def update_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        # Сортировка по Tag (eq_name) по возрастанию
        sorted_equips = sorted(self.filtered_equips, key=lambda eq: str(eq.get('eq_name', '')))
        for eq in sorted_equips:
            values = (
                eq.get('eq_name', ''),
                eq.get('plc_name', ''),
                eq.get('db_num', ''),
                eq.get('db_addr', '')
            )
            self.tree.insert('', tk.END, values=values)

    # --- Выбор и действия с оборудованием ---
    def on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            self.add_log(f"Выбрано оборудование: {values[0]}")
            # Find the selected equipment in filtered list
            for eq in self.filtered_equips:
                if eq.get('eq_name', '') == values[0]:
                    self.selected_equip = eq
                    break
        else:
            self.selected_equip = None

    def on_double_click(self, event):
        # Get the item under cursor
        item = self.tree.identify('item', event.x, event.y)
        if item:
            # Select the item first
            self.tree.selection_set(item)
            # Then read PLC data
            self.read_plc_data()

    # --- Работа с PLC ---
    def get_plc_connection_params(self, plc_name):
        for plc in self.plc_configs:
            if plc.get('plc_name') == plc_name:
                return plc.get('plc_addr'), plc.get('rack', 0), plc.get('slot', 1)
        return None, 0, 1  # По умолчанию

    def read_plc_data(self):
        if not self.selected_equip:
            self.add_log("ПРЕДУПРЕЖДЕНИЕ: Выберите оборудование в таблице!")
            return
        try:
            # Create PLC client
            client = snap7.client.Client()
            # Получаем параметры подключения из plc.json по plc_name
            plc_name = self.selected_equip.get('plc_name', '')
            plc_addr, rack, slot = self.get_plc_connection_params(plc_name)
            if not plc_addr:
                self.add_log(f"ОШИБКА: Не найдены параметры PLC для '{plc_name}' в plc.json")
                return
            self.add_log(f"Подключение к PLC {plc_addr} (rack={rack}, slot={slot})...")
            client.connect(plc_addr, rack, slot)
            if client.get_connected():
                # Read DINT value from DB
                db_num = self.selected_equip['db_num']
                db_addr = self.selected_equip['db_addr']
                self.add_log(f"Чтение DB{db_num}.DBD{db_addr}...")
                # Read 4 bytes (DINT = 32 bits = 4 bytes)
                data = client.db_read(db_num, db_addr, 4)
                # Convert to DINT
                dint_value = get_dint(data, 0)
                # Update result label
                self.result_entry.config(state="normal")
                self.result_var.set(str(dint_value))
                self.result_entry.config(state="readonly")
                # Convert seconds to hours and update hours field
                hours = dint_value / 3600.0
                self.hours_var.set(f"{hours:.2f}")
                self.add_log(f"Прочитано: {dint_value} сек ({hours:.2f} ч) из {self.selected_equip['eq_name']}")
                # Disconnect
                client.disconnect()
                self.add_log("Отключение от PLC")
            else:
                self.add_log(f"ОШИБКА: Не удалось подключиться к PLC {plc_addr}")
        except Exception as e:
            self.add_log(f"ОШИБКА при чтении данных: {str(e)}")

    def write_plc_data(self):
        if not self.selected_equip:
            self.add_log("ПРЕДУПРЕЖДЕНИЕ: Выберите оборудование в таблице!")
            return
        try:
            # Get hours value and convert to seconds
            hours_str = self.hours_var.get().strip()
            if not hours_str:
                self.add_log("ПРЕДУПРЕЖДЕНИЕ: Введите значение в поле 'Часы'!")
                return
            hours = float(hours_str)
            if not (0 <= hours <= 10000):
                self.add_log("ПРЕДУПРЕЖДЕНИЕ: Значение часов должно быть от 0 до 10000!")
                return
            seconds = int(hours * 3600)  # Convert hours to seconds
            self.add_log(f"Подготовка записи: {hours:.2f} ч = {seconds} сек")
            # Create PLC client
            client = snap7.client.Client()
            # Получаем параметры подключения из plc.json по plc_name
            plc_name = self.selected_equip.get('plc_name', '')
            plc_addr, rack, slot = self.get_plc_connection_params(plc_name)
            if not plc_addr:
                self.add_log(f"ОШИБКА: Не найдены параметры PLC для '{plc_name}' в plc.json")
                return
            self.add_log(f"Подключение к PLC {plc_addr} (rack={rack}, slot={slot})...")
            client.connect(plc_addr, rack, slot)
            if client.get_connected():
                # Write DINT value to DB
                db_num = self.selected_equip['db_num']
                db_addr = self.selected_equip['db_addr']
                self.add_log(f"Запись в DB{db_num}.DBD{db_addr}...")
                # Convert seconds to bytes for DINT
                data = bytearray(4)
                set_dint(data, 0, seconds)
                # Write to PLC
                client.db_write(db_num, db_addr, data)
                self.add_log(f"УСПЕХ: Записано {seconds} сек ({hours:.2f} ч) в {self.selected_equip['eq_name']}")
                # Read data back to confirm
                self.read_plc_data()
                # Disconnect
                client.disconnect()
                self.add_log("Отключение от PLC")
            else:
                self.add_log(f"ОШИБКА: Не удалось подключиться к PLC {plc_addr}")
        except ValueError:
            self.add_log("ОШИБКА: Неверное значение в поле 'Часы'. Введите число.")
        except Exception as e:
            self.add_log(f"ОШИБКА при записи данных: {str(e)}")

    def validate_hours(self, value: str) -> bool:
        if value == '':
            return True
        try:
            val = float(value)
            return 0 <= val <= 10000
        except ValueError:
            return False


    def show_help(self):
        description = (
            "Редактор часов тех обслуживания ЗИФ 1 и 2\n\n"
            "Список оборудования с именами тегов и адресами DBxx.DBDxx хранится в файле equips.json\n\n"
            "IP адреса ПЛК и настройки подключения хранятся в файле plc.json.\n\n"
            "semonoff@gmail.com \n"
            "7Art 2025\n"

        )
        messagebox.showinfo("О программе", description )

if __name__ == '__main__':
    app = RHEditor()
    app.mainloop() 