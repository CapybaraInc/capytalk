import requests
import os
from datetime import datetime

SERVER = "https://capytalk.onrender.com"
token = None
username = None

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def register():
    u = input("Логин: ").strip().lower()
    p = input("Пароль: ").strip()
    r = requests.post(f"{SERVER}/register", json={"username": u, "password": p})
    if r.json().get('success'):
        print("✅ Зарегистрирован! Войди.")
    else:
        print("❌ Ошибка")

def login():
    global token, username
    u = input("Логин: ").strip().lower()
    p = input("Пароль: ").strip()
    r = requests.post(f"{SERVER}/login", json={"username": u, "password": p})
    d = r.json()
    if d.get('success'):
        token = d['token']
        username = d['username']
        print(f"✅ Привет, {username}!")
        return True
    else:
        print("❌ Неверно")
        return False

def show_users():
    r = requests.get(f"{SERVER}/users?token={token}")
    users = r.json()
    for i, u in enumerate(users, 1):
        print(f"{i}. {u}")
    return users

def show_groups():
    r = requests.get(f"{SERVER}/groups?token={token}")
    groups = r.json()
    for i, g in enumerate(groups, 1):
        print(f"{i}. {g['name']} ({g['cnt']} уч.)")
    return groups

def chats():
    r = requests.get(f"{SERVER}/chats?token={token}")
    chats = r.json()
    for i, c in enumerate(chats, 1):
        icon = "👥" if c['type'] == 'group' else "👤"
        print(f"{i}. {icon} {c['name']}")
    return chats

def chat_with(uid, ctype='private'):
    r = requests.get(f"{SERVER}/messages?token={token}&chat_type={ctype}&chat_id={uid}")
    msgs = r.json()
    clear()
    for msg in msgs[-20:]:
        s = "→" if msg['s'] == username else "←"
        print(f"[{msg['tm']}] {s} {msg['s']}: {msg['t']}")
    print("-"*30)
    while True:
        txt = input("> ").strip()
        if txt == '/back':
            break
        if txt:
            requests.post(f"{SERVER}/send_message", json={
                "token": token, "chat_type": ctype,
                "chat_id": uid, "text": txt
            })
            print(f"[Сейчас] → Ты: {txt}")

def create_group():
    name = input("Название группы: ").strip()
    r = requests.post(f"{SERVER}/create_group", json={"token": token, "group_name": name})
    d = r.json()
    if d.get('success'):
        print(f"✅ Группа создана! ID: {d['id']}")

def join_group():
    gid = input("ID группы: ").strip()
    requests.post(f"{SERVER}/join_group", json={"token": token, "group_id": gid})
    print("✅ Вступил!")

def main():
    while True:
        clear()
        print("🐹 CapyTalk")
        print("1. Регистрация\n2. Вход\n3. Выход")
        c = input("> ")
        if c == '1': register()
        elif c == '2':
            if login(): break
        elif c == '3': return
        input("Enter...")

    while True:
        clear()
        print(f"👤 {username}")
        print("1. Чаты\n2. Контакты\n3. Группы\n4. Создать группу\n5. Вступить\n6. Выйти")
        c = input("> ")
        if c == '1':
            lst = chats()
            if lst:
                n = input("Номер: ")
                if n.isdigit() and 0 < int(n) <= len(lst):
                    cht = lst[int(n)-1]
                    chat_with(cht['id'], cht['type'])
        elif c == '2':
            lst = show_users()
            n = input("Номер: ")
            if n.isdigit() and 0 < int(n) <= len(lst):
                chat_with(lst[int(n)-1], 'private')
        elif c == '3':
            lst = show_groups()
            n = input("Номер: ")
            if n.isdigit() and 0 < int(n) <= len(lst):
                chat_with(lst[int(n)-1]['id'], 'group')
        elif c == '4': create_group()
        elif c == '5': join_group()
        elif c == '6': break
        input("Enter...")

if __name__ == '__main__':
    main()
