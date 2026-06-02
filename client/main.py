"""
CapyTalk Client — приложение на Flet
Запуск: flet run main.py (десктоп / браузер)
Сборка: flet build apk --package com.capytalk.app --name CapyTalk
"""

import flet as ft
import json
import threading
from datetime import datetime
from websocket import WebSocketApp

# ─── Конфигурация ───
SERVER_URL = "ws://192.168.1.100:8000"  # Замени на IP своего сервера
# Для локального теста используй: ws://127.0.0.1:8000
# Для телефона в одной сети укажи IP компьютера с сервером

class CapyTalkClient:
    """Управляет WebSocket-соединением и хранит состояние чата"""
    
    def __init__(self):
        self.ws: WebSocketApp = None
        self.username: str = ""
        self.messages: list = []
        self.on_message_callback = None
        self.on_connected_callback = None
    
    def connect(self, username: str):
        self.username = username
        url = f"{SERVER_URL}/ws/{username}"
        
        def on_open(ws):
            print("Подключено к серверу")
            if self.on_connected_callback:
                self.on_connected_callback()
        
        def on_message(ws, message):
            data = json.loads(message)
            self.messages.append(data)
            if self.on_message_callback:
                self.on_message_callback(data)
        
        def on_error(ws, error):
            print(f"Ошибка: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print("Соединение закрыто")
        
        self.ws = WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()
    
    def send(self, text: str):
        if self.ws:
            self.ws.send(json.dumps({"text": text}))


# ─── UI Приложение ───
def main(page: ft.Page):
    page.title = "🐹 CapyTalk"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.END
    page.horizontal_alignment = ft.Stretch
    page.padding = 0
    
    client = CapyTalkClient()
    
    # ─── Компоненты ───
    chat_view = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
        padding=15
    )
    
    message_input = ft.TextField(
        hint_text="Напиши сообщение...",
        expand=True,
        border_radius=25,
        filled=True,
        shift_enter=True,
        min_lines=1,
        max_lines=4,
        on_submit=lambda e: send_message(e)  # Enter = отправить
    )
    
    send_button = ft.IconButton(
        icon=ft.icons.SEND_ROUNDED,
        icon_color=ft.colors.BLUE,
        on_click=lambda e: send_message(e)
    )
    
    # Статус-бар
    status_text = ft.Text("🔴 Не подключен", size=12, italic=True)
    
    # ─── Экран входа ───
    username_field = ft.TextField(
        label="Твой никнейм",
        hint_text="Капибара_42",
        border_radius=25,
        width=300,
        autofocus=True,
        on_submit=lambda e: join_chat(e)
    )
    
    join_button = ft.ElevatedButton(
        "🐹 Войти в чат",
        on_click=lambda e: join_chat(e),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25))
    )
    
    login_view = ft.Column(
        [
            ft.Icon(ft.icons.CHAT_BUBBLE, size=80, color=ft.colors.BLUE),
            ft.Text("CapyTalk", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Мессенджер для дружелюбного общения", size=14, color=ft.colors.GREY),
            ft.Container(height=30),
            username_field,
            ft.Container(height=10),
            join_button
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    
    chat_ui = ft.Column(
        [
            # Верхняя панель
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text("🐹 CapyTalk", size=18, weight=ft.FontWeight.BOLD),
                        status_text
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=15,
                bgcolor=ft.colors.SURFACE_VARIANT,
            ),
            # Область сообщений
            chat_view,
            # Панель ввода
            ft.Container(
                content=ft.Row(
                    [message_input, send_button],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                padding=10,
                border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.OUTLINE_VARIANT))
            )
        ],
        expand=True,
        visible=False
    )
    
    page.add(login_view, chat_ui)
    
    # ─── Функции ───
    def join_chat(e):
        username = username_field.value.strip()
        if not username:
            username_field.error_text = "Введи никнейм!"
            page.update()
            return
        if " " in username:
            username_field.error_text = "Никнейм без пробелов!"
            page.update()
            return
        
        # Подключаемся
        client.on_connected_callback = on_connected
        client.on_message_callback = on_new_message
        client.connect(username)
        
        # Меняем экран
        login_view.visible = False
        chat_ui.visible = True
        page.title = f"🐹 CapyTalk — {username}"
        page.update()
    
    def on_connected():
        status_text.value = "🟢 Онлайн"
        status_text.color = ft.colors.GREEN
        page.update()
    
    def on_new_message(data):
        msg_type = data.get("type", "message")
        
        if msg_type == "system":
            chat_view.controls.append(
                ft.Container(
                    content=ft.Text(
                        data.get("text", ""),
                        size=13,
                        italic=True,
                        color=ft.colors.GREY_700,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(vertical=5)
                )
            )
        else:
            is_me = data.get("username") == client.username
            username = "Вы" if is_me else data.get("username", "кто-то")
            
            bubble = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(username, size=12, weight=ft.FontWeight.BOLD,
                                color=ft.colors.WHITE if is_me else ft.colors.BLUE),
                        ft.Text(data.get("text", ""), size=15, color=ft.colors.WHITE if is_me else ft.colors.BLACK),
                        ft.Text(data.get("time", ""), size=10,
                                color=ft.colors.WHITE70 if is_me else ft.colors.GREY_500)
                    ],
                    tight=True,
                    spacing=2
                ),
                padding=ft.padding.all(12),
                border_radius=ft.border_radius.only(
                    top_left=20,
                    top_right=20,
                    bottom_left=5 if is_me else 20,
                    bottom_right=20 if is_me else 5
                ),
                bgcolor=ft.colors.BLUE_700 if is_me else ft.colors.GREY_200,
                margin=ft.margin.only(left=50 if is_me else 0, right=0 if is_me else 50, bottom=5),
                animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
            )
            
            chat_view.controls.append(bubble)
        
        page.update()
    
    def send_message(e):
        text = message_input.value.strip()
        if text:
            client.send(text)
            message_input.value = ""
            message_input.focus()
            page.update()

# ─── Запуск ───
if __name__ == "__main__":
    ft.app(target=main)
