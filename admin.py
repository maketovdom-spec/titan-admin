import os
import json
import hashlib
import uuid
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.metrics import dp

# ============================================================================
# НАСТРОЙКИ И ТЕМА
# ============================================================================
Window.clearcolor = (0.12, 0.12, 0.15, 1)
COLOR_TEXT = (1, 1, 1, 1)
COLOR_ACCENT = (0.9, 0.7, 0.2, 1)
COLOR_SUCCESS = (0.2, 0.9, 0.2, 1)
COLOR_DANGER = (0.9, 0.2, 0.2, 1)
COLOR_WARN = (0.9, 0.5, 0.2, 1)
COLOR_GRAY = (0.5, 0.5, 0.5, 1)

SECRET_KEY = "TITAN_PRO_SECRET_2026_NEVINNOMYSSK"
DB_FILE_NAME = "titan_clients_db.json"

# ============================================================================
# БАЗА ДАННЫХ
# ============================================================================
class Database:
    @staticmethod
    def get_db_path():
        app = App.get_running_app()
        return os.path.join(app.user_data_dir, DB_FILE_NAME)

    @staticmethod
    def load():
        path = Database.get_db_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"clients": []}
        return {"clients": []}

    @staticmethod
    def save(data):
        path = Database.get_db_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def add_client(name, device_id, notes=""):
        db = Database.load()
        signature = hashlib.sha256((device_id.upper() + SECRET_KEY).encode()).hexdigest()
        key = f"TITAN-{device_id[:4].upper()}-{device_id[4:8].upper()}-{signature[:8].upper()}"
        new_client = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "device_id": device_id.upper(),
            "key": key,
            "status": "active",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "notes": notes
        }
        db["clients"].append(new_client)
        Database.save(db)
        return new_client

    @staticmethod
    def toggle_status(client_id):
        db = Database.load()
        for c in db["clients"]:
            if c["id"] == client_id:
                c["status"] = "blocked" if c["status"] == "active" else "active"
                break
        Database.save(db)

    @staticmethod
    def delete_client(client_id):
        db = Database.load()
        db["clients"] = [c for c in db["clients"] if c["id"] != client_id]
        Database.save(db)

# ============================================================================
# UI: КАРТОЧКА КЛИЕНТА
# ============================================================================
class ClientCard(BoxLayout):
    def __init__(self, client_data, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(140)
        self.padding = dp(12)
        self.spacing = dp(8)
        
        top_row = BoxLayout(size_hint_y=None, height=dp(35))
        top_row.add_widget(Label(text=client_data['name'], font_size=dp(18), bold=True, halign='left', color=COLOR_TEXT))
        status_color = COLOR_SUCCESS if client_data['status'] == 'active' else COLOR_DANGER
        status_text = "АКТИВЕН" if client_data['status'] == 'active' else "БЛОК"
        top_row.add_widget(Label(text=status_text, font_size=dp(14), bold=True, color=status_color, halign='right'))
        self.add_widget(top_row)

        mid_row = BoxLayout(size_hint_y=None, height=dp(30))
        mid_row.add_widget(Label(text=f"ID: {client_data['device_id']}", font_size=dp(13), color=COLOR_GRAY, halign='left'))
        mid_row.add_widget(Label(text=client_data['created'], font_size=dp(12), color=COLOR_GRAY, halign='right'))
        self.add_widget(mid_row)

        key_row = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(10))
        key_row.add_widget(Label(text=client_data['key'], font_size=dp(11), color=COLOR_ACCENT, halign='left'))
        btn_copy = Button(text="КОПИРОВАТЬ", font_size=dp(12), bold=True, background_color=COLOR_ACCENT, size_hint_x=0.35)
        btn_copy.bind(on_press=lambda x: self.copy_key(client_data['key'], btn_copy))
        key_row.add_widget(btn_copy)
        self.add_widget(key_row)

        ctrl_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        btn_block = Button(text="БЛОКИРОВАТЬ" if client_data['status'] == 'active' else "РАЗБЛОКИРОВАТЬ", 
                           font_size=dp(14), background_color=COLOR_WARN)
        btn_block.bind(on_press=lambda x: self.action_block(client_data['id']))
        ctrl_row.add_widget(btn_block)

        btn_del = Button(text="УДАЛИТЬ", font_size=dp(14), background_color=COLOR_DANGER)
        btn_del.bind(on_press=lambda x: self.action_delete(client_data['id']))
        ctrl_row.add_widget(btn_del)
        self.add_widget(ctrl_row)

    def copy_key(self, key, btn):
        Clipboard.copy(key)
        old_text = btn.text
        btn.text = "СКОПИРОВАНО!"
        btn.background_color = COLOR_SUCCESS
        Clock.schedule_once(lambda dt: setattr(btn, 'text', old_text) or setattr(btn, 'background_color', COLOR_ACCENT), 2)

    def action_block(self, cid):
        Database.toggle_status(cid)
        App.get_running_app().refresh_clients()

    def action_delete(self, cid):
        Database.delete_client(cid)
        App.get_running_app().refresh_clients()

# ============================================================================
# ЭКРАНЫ
# ============================================================================
class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        layout.add_widget(Label(text="TITAN Admin", font_size=dp(36), bold=True, color=COLOR_ACCENT, size_hint_y=None, height=dp(80)))
        self.stats_label = Label(text="Загрузка...", font_size=dp(22), color=COLOR_TEXT, halign='center')
        layout.add_widget(self.stats_label)
        self.add_widget(layout)

    def on_enter(self):
        db = Database.load()
        total = len(db["clients"])
        active = sum(1 for c in db["clients"] if c["status"] == "active")
        blocked = total - active
        self.stats_label.text = (
            f"Всего клиентов: {total}\n\n"
            f"АКТИВНЫ: {active}\n"
            f"ЗАБЛОКИРОВАНЫ: {blocked}"
        )

class ClientsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        header = BoxLayout(size_hint_y=None, height=dp(50))
        header.add_widget(Label(text="База клиентов", font_size=dp(22), bold=True, color=COLOR_TEXT))
        self.add_widget(header)
        
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15), padding=dp(5))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def on_enter(self):
        self.load_clients()

    def load_clients(self):
        self.list_layout.clear_widgets()
        db = Database.load()
        if not db["clients"]:
            self.list_layout.add_widget(Label(text="База пуста. Добавьте первого клиента.", color=COLOR_GRAY, size_hint_y=None, height=dp(50)))
            return
        for client in reversed(db["clients"]):
            self.list_layout.add_widget(ClientCard(client))

class GenerateScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        layout.add_widget(Label(text="Выдача лицензии", font_size=dp(26), bold=True, color=COLOR_ACCENT, size_hint_y=None, height=dp(60)))
        
        self.in_name = TextInput(hint_text="Имя клиента", font_size=dp(18), size_hint_y=None, height=dp(55), background_color=(0.2, 0.2, 0.2, 1))
        layout.add_widget(self.in_name)
        
        self.in_device = TextInput(hint_text="Device ID (12 символов)", font_size=dp(18), size_hint_y=None, height=dp(55), background_color=(0.2, 0.2, 0.2, 1))
        layout.add_widget(self.in_device)
        
        self.in_notes = TextInput(hint_text="Заметки (необязательно)", font_size=dp(16), size_hint_y=None, height=dp(55), background_color=(0.2, 0.2, 0.2, 1))
        layout.add_widget(self.in_notes)
        
        self.result_label = Label(text="", font_size=dp(16), color=COLOR_SUCCESS, size_hint_y=None, height=dp(60))
        layout.add_widget(self.result_label)
        
        btn = Button(text="СГЕНЕРИРОВАТЬ КЛЮЧ", font_size=dp(20), bold=True, background_color=COLOR_SUCCESS, size_hint_y=None, height=dp(65))
        btn.bind(on_press=self.do_generate)
        layout.add_widget(btn)
        
        self.add_widget(layout)

    def do_generate(self, instance):
        name = self.in_name.text.strip()
        device = self.in_device.text.strip().upper()
        notes = self.in_notes.text.strip()
        
        if not name or len(device) != 12:
            self.result_label.text = "Ошибка: Заполните имя и Device ID (12 символов)!"
            self.result_label.color = COLOR_DANGER
            return
            
        client = Database.add_client(name, device, notes)
        self.result_label.text = f"Ключ создан и скопирован:\n{client['key']}"
        self.result_label.color = COLOR_SUCCESS
        Clipboard.copy(client['key'])
        
        self.in_name.text = ""
        self.in_device.text = ""
        self.in_notes.text = ""

# ============================================================================
# APP
# ============================================================================
class TitanAdminApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name='dash'))
        sm.add_widget(ClientsScreen(name='clients'))
        sm.add_widget(GenerateScreen(name='gen'))
        
        root = BoxLayout(orientation='vertical')
        root.add_widget(sm)
        
        nav = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(5), padding=dp(5))
        for name, title in [('dash', 'Статистика'), ('clients', 'Клиенты'), ('gen', 'Выдать')]:
            btn = Button(text=title, font_size=dp(16), bold=True, background_color=COLOR_ACCENT)
            btn.bind(on_press=lambda x, n=name: setattr(sm, 'current', n))
            nav.add_widget(btn)
        root.add_widget(nav)
        
        return root

    def refresh_clients(self):
        sm = self.root.children[0]
        clients_screen = sm.get_screen('clients')
        if clients_screen:
            clients_screen.load_clients()

if __name__ == '__main__':
    TitanAdminApp().run()
