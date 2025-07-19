import tkinter as tk
from tkinter import ttk, messagebox
import yaml
import os
import snap7
from snap7.util import *

EQUIPS_FILE = 'rh_editor/equips.yaml'

class EquipViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Equipments Viewer')
        self.geometry('700x400')
        self.equips = []
        self.filtered_equips = []
        self.selected_equip = None
        self.create_widgets()
        self.load_equips()
        self.update_table()

    def create_widgets(self):
        # Filter label and entry
        filter_frame = tk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(filter_frame, text='Фильтр по eq_name:').pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add('write', self.on_filter_change)
        filter_entry = tk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Table
        columns = ('eq_name', 'plc_name', 'plc_addr', 'db_num', 'db_addr')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # Bind double-click event
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Read button and result label
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.read_button = tk.Button(button_frame, text="READ", command=self.read_plc_data)
        self.read_button.pack(side=tk.LEFT)
        
        self.write_button = tk.Button(button_frame, text="WRITE", command=self.write_plc_data, 
                                    bg="red", fg="white", font=("Arial", 10, "bold"))
        self.write_button.pack(side=tk.LEFT, padx=10)
        
        self.result_label = tk.Label(button_frame, text="Результат: ", font=("Arial", 10, "bold"))
        self.result_label.pack(side=tk.LEFT, padx=10)
        
        # Hours display
        tk.Label(button_frame, text="Часы: ", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.hours_var = tk.StringVar()
        self.hours_entry = tk.Entry(button_frame, textvariable=self.hours_var, width=15)
        self.hours_entry.pack(side=tk.LEFT, padx=5)
        
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

    def add_log(self, message):
        """Add message to log area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)  # Scroll to bottom
        self.log_text.config(state=tk.DISABLED)

    def load_equips(self):
        if not os.path.exists(EQUIPS_FILE):
            self.add_log(f'ОШИБКА: Файл {EQUIPS_FILE} не найден!')
            self.equips = []
            return
        with open(EQUIPS_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.equips = data.get('equips', [])
        self.filtered_equips = self.equips.copy()
        self.add_log(f'Загружено {len(self.equips)} записей оборудования')

    def update_table(self):
        self.tree.delete(*self.tree.get_children())
        for eq in self.filtered_equips:
            values = (
                eq.get('eq_name', ''),
                eq.get('plc_name', ''),
                eq.get('plc_addr', ''),
                eq.get('db_num', ''),
                eq.get('db_addr', '')
            )
            self.tree.insert('', tk.END, values=values)

    def on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            # Find the selected equipment in filtered list
            for eq in self.filtered_equips:
                if (eq.get('eq_name', '') == values[0] and 
                    eq.get('plc_name', '') == values[1] and
                    eq.get('plc_addr', '') == values[2] and
                    eq.get('db_num', '') == values[3] and
                    eq.get('db_addr', '') == values[4]):
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

    def read_plc_data(self):
        if not self.selected_equip:
            self.add_log("ПРЕДУПРЕЖДЕНИЕ: Выберите оборудование в таблице!")
            return
            
        try:
            # Create PLC client
            client = snap7.client.Client()
            
            # Connect to PLC
            plc_addr = self.selected_equip['plc_addr']
            self.add_log(f"Подключение к PLC {plc_addr}...")
            client.connect(plc_addr, 0, 1)  # IP, rack, slot
            
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
                self.result_label.config(text=f"Результат: {dint_value}")
                
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
            seconds = int(hours * 3600)  # Convert hours to seconds
            
            self.add_log(f"Подготовка записи: {hours:.2f} ч = {seconds} сек")
            
            # Create PLC client
            client = snap7.client.Client()
            
            # Connect to PLC
            plc_addr = self.selected_equip['plc_addr']
            self.add_log(f"Подключение к PLC {plc_addr}...")
            client.connect(plc_addr, 0, 1)  # IP, rack, slot
            
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

    def on_filter_change(self, *args):
        filter_text = self.filter_var.get().strip().lower()
        if not filter_text:
            self.filtered_equips = self.equips.copy()
        else:
            self.filtered_equips = [
                eq for eq in self.equips
                if filter_text in str(eq.get('eq_name', '')).lower()
            ]
        self.update_table()

if __name__ == '__main__':
    app = EquipViewer()
    app.mainloop() 