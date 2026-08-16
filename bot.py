import requests
import time
import json
import random
import uuid
import telebot
import threading
from datetime import datetime

TOKEN = "8966832519:AAHXipG38GAUO4hwlRGnBNkVqLz2ZjJcGXE"
ADMIN_ID = "8989779683"

bot = telebot.TeleBot(TOKEN)

class TikTokBot:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://www.tiktok.com',
            'Referer': 'https://www.tiktok.com/',
            'Content-Type': 'application/json'
        })
        self.sessionid = ''
        self.groups = []
        self.messages = []
        self.sent = 0
        self.failed = 0
        self.is_running = False
        self.delay = 60
        self.selected = []

tool = TikTokBot()

@bot.message_handler(commands=['start'])
def start(message):
    if str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, "Khong co quyen!")
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Dang nhap', 'Lay nhom')
    markup.row('Nhap noi dung', 'Spam tin')
    markup.row('Dung', 'Thong ke')
    
    bot.send_message(message.chat.id, "TIKTOK SPAM BOT\n\nChon chuc nang:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Dang nhap')
def login_handler(message):
    msg = bot.reply_to(message, "Nhap sessionid:")
    bot.register_next_step_handler(msg, process_login)

def process_login(message):
    sessionid = message.text.strip()
    tool.sessionid = sessionid
    tool.session.cookies.set('sessionid', sessionid, domain='.tiktok.com')
    
    bot.reply_to(message, "Da luu!\nDang lay nhom...")
    
    try:
        response = tool.session.get('https://www.tiktok.com/api/msg/list/', params={'aid': '1988', 'cursor': '0', 'count': '50'})
        
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversationList', [])
            
            if conversations:
                tool.groups = []
                for conv in conversations:
                    user = conv.get('user', {})
                    tool.groups.append({
                        'conv_id': str(conv.get('conversation_id', '')),
                        'user_id': str(user.get('id', '')),
                        'name': user.get('uniqueId', 'Unknown')
                    })
                
                group_text = "\n".join([f"{i+1}. @{g['name']}" for i, g in enumerate(tool.groups)])
                bot.reply_to(message, f"Lay duoc {len(tool.groups)} nhom:\n\n{group_text}")
            else:
                bot.reply_to(message, "Khong lay duoc nhom!\nNhap user IDs:")
                bot.register_next_step_handler(message, process_manual)
    except Exception as e:
        bot.reply_to(message, f"Loi: {e}")

def process_manual(message):
    user_ids = [uid.strip() for uid in message.text.split(',') if uid.strip()]
    if user_ids:
        tool.groups = []
        for uid in user_ids:
            tool.groups.append({'conv_id': '', 'user_id': uid, 'name': f'User_{uid[:8]}'})
        bot.reply_to(message, f"Da them {len(user_ids)} users!")

@bot.message_handler(func=lambda m: m.text == 'Lay nhom')
def groups_handler(message):
    if not tool.groups:
        bot.reply_to(message, "Chua co nhom!")
        return
    group_text = "\n".join([f"{i+1}. @{g['name']}" for i, g in enumerate(tool.groups)])
    bot.reply_to(message, f"DANH SACH NHOM:\n\n{group_text}")

@bot.message_handler(func=lambda m: m.text == 'Nhap noi dung')
def content_handler(message):
    msg = bot.reply_to(message, "Nhap noi dung (cach nhau bang |):")
    bot.register_next_step_handler(msg, process_content)

def process_content(message):
    content = message.text.strip()
    tool.messages = [line.strip() for line in content.split('|') if line.strip()]
    if not tool.messages:
        tool.messages = [content]
    bot.reply_to(message, f"Da luu {len(tool.messages)} tin!")
    msg = bot.reply_to(message, "Nhap delay (giay):")
    bot.register_next_step_handler(msg, process_delay)

def process_delay(message):
    try:
        tool.delay = float(message.text.strip())
    except:
        tool.delay = 60
    bot.reply_to(message, f"Delay: {tool.delay}s!\nBam 'Spam tin' de gui!")

@bot.message_handler(func=lambda m: m.text == 'Spam tin')
def send_handler(message):
    if not tool.groups:
        bot.reply_to(message, "Chua co nhom!")
        return
    if not tool.messages:
        bot.reply_to(message, "Chua co noi dung!")
        return
    group_text = "\n".join([f"{i+1}. @{g['name']}" for i, g in enumerate(tool.groups)])
    msg = bot.reply_to(message, f"Chon nhom (so hoac 'all'):\n\n{group_text}")
    bot.register_next_step_handler(msg, process_select)

def process_select(message):
    choice = message.text.strip()
    if choice.lower() == 'all':
        tool.selected = tool.groups
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip()]
            tool.selected = [tool.groups[idx] for idx in indices if 0 <= idx < len(tool.groups)]
        except:
            bot.reply_to(message, "Loi chon!")
            return
    if not tool.selected:
        bot.reply_to(message, "Khong co nhom!")
        return
    tool.is_running = True
    bot.reply_to(message, f"BAT DAU SPAM!\nBam 'Dung' de dung!")
    threading.Thread(target=send_loop, args=(message.chat.id,)).start()

def send_loop(chat_id):
    round_count = 0
    while tool.is_running:
        round_count += 1
        for target in tool.selected:
            for msg in tool.messages:
                success, result = send_msg(target['user_id'], msg, target.get('conv_id', ''))
                timestamp = datetime.now().strftime('%H:%M:%S')
                if success:
                    text = f"[{timestamp}] OK @{target['name']}: {msg[:30]}"
                else:
                    text = f"[{timestamp}] FAIL @{target['name']}: {result}"
                try:
                    bot.send_message(chat_id, text)
                except:
                    pass
                time.sleep(random.uniform(1, 3))
        try:
            bot.send_message(chat_id, f"Xong vong {round_count}\nCho {tool.delay}s...")
        except:
            pass
        time.sleep(tool.delay)

def send_msg(user_id, message, conv_id=''):
    try:
        url = "https://www.tiktok.com/api/msg/send_message/"
        params = {
            'aid': '1988',
            'app_language': 'vi-VN',
            'app_name': 'tiktok_web',
            'device_id': str(uuid.uuid4()),
            'device_platform': 'web_pc',
            'language': 'vi-VN',
            'region': 'VN',
            'msToken': uuid.uuid4().hex + uuid.uuid4().hex
        }
        data = {
            'content': message,
            'to_user_id': user_id,
            'session_id': conv_id,
            'client_message_id': str(uuid.uuid4()),
            'send_msg_timestamp': int(time.time() * 1000)
        }
        response = tool.session.post(url, params=params, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('status_code') == 0:
                tool.sent += 1
                return True, "OK"
            else:
                tool.failed += 1
                return False, result.get('status_msg', 'Loi')
        else:
            tool.failed += 1
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        tool.failed += 1
        return False, str(e)

@bot.message_handler(func=lambda m: m.text == 'Dung')
def stop_handler(message):
    tool.is_running = False
    bot.reply_to(message, "Da dung!")

@bot.message_handler(func=lambda m: m.text == 'Thong ke')
def stats_handler(message):
    bot.reply_to(message, f"OK: {tool.sent}\nFail: {tool.failed}")

print("Bot dang chay...")
bot.polling(none_stop=True)
