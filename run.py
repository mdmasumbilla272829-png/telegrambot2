import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import string
import datetime
import time
import uuid
from functools import wraps

# Middleware চালু করার জন্য এই লাইনটি যোগ করা হয়েছে
telebot.apihelper.ENABLE_MIDDLEWARE = True

# অনুগ্রহ করে এখানে আপনার আসল এবং সঠিক বট টোকেনটি বসান
API_TOKEN = "8423406313:AAHLlI8Cx9yaeSGoz79OeUtY-rVxCisSFXI"

# অ্যাডমিন প্যানেলে প্রবেশের জন্য পাসওয়ার্ড
ADMIN_PASSWORD = "@Mo321321@###"

# ডেটা সংরক্ষণের জন্য ফাইলের নাম
USER_DATA_FILE = 'users.json'
CONFIG_FILE = 'config.json'

# বট অবজেক্ট তৈরি করা
bot = telebot.TeleBot(API_TOKEN, parse_mode='Markdown')

# -----------------------------------------------------------------------------
# ডেটা ম্যানেজমেন্ট ফাংশন
# -----------------------------------------------------------------------------

def load_user_data():
    if not os.path.exists(USER_DATA_FILE): return {}
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_config():
    default_config = {'welcome_coin_bonus': 300, 'welcome_dk_bonus': 50}
    if not os.path.exists(CONFIG_FILE): return default_config
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_config

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def generate_unique_id():
    return ''.join(random.choices(string.digits, k=11))

def generate_notification_id():
    return str(uuid.uuid4())

users = load_user_data()
config = load_config()
admin_actions = {}

# -----------------------------------------------------------------------------
# নতুন ডেকোরেটর (Decorator) ব্লক ইউজার চেক করার জন্য
# -----------------------------------------------------------------------------

def block_check_decorator(func):
    @wraps(func)
    def decorated_function(message, *args, **kwargs):
        user_id = str(message.from_user.id)
        # অ্যাডমিন পাসওয়ার্ড ছাড়া অন্য সব ক্ষেত্রে ব্লক চেক করা হবে
        if message.text != ADMIN_PASSWORD and user_id in users and users[user_id].get('blocked', False):
            bot.send_message(message.chat.id, "❌ *You are currently blocked from using this bot.*")
            return  # এখানে থেমে যাবে এবং কোনো এরর দেখাবে না
        return func(message, *args, **kwargs)
    return decorated_function

# -----------------------------------------------------------------------------
# ডিজাইন এবং স্টাইল (Design and Style)
# -----------------------------------------------------------------------------

def create_styled_text(title, body):
    header = f"╭─── ⋅ ⋅ ─── ❖ ─── ⋅ ⋅ ───╮\n      {title}\n╰─── ⋅ ⋅ ─── ❖ ─── ⋅ ⋅ ───╯"
    content = f"\n{body}\n"
    footer = "═══════════════════════"
    return f"{header}\n{content}\n{footer}"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def find_user(query):
    for user_id, data in users.items():
        if str(user_id) == query or data.get('custom_id') == query or (data.get('username') and data.get('username').lower() == query.lower().replace('@', '')):
            return user_id, data
    return None, None

def parse_expiry_time(text):
    if not text or text.lower() == 'none': return None
    try:
        value, unit = text.lower().split()
        value = int(value)
        now = datetime.datetime.now()
        delta_map = {'sec': 'seconds', 'min': 'minutes', 'hour': 'hours', 'day': 'days', 'month': 'days', 'year': 'days'}
        unit_key = next((k for k in delta_map if k in unit), None)
        if not unit_key: return None
        if unit_key == 'month': value *= 30
        if unit_key == 'year': value *= 365
        delta = datetime.timedelta(**{delta_map[unit_key]: value})
        return int((now + delta).timestamp())
    except Exception:
        return None

# -----------------------------------------------------------------------------
# কীবোর্ড (Buttons) তৈরির সেকশন
# -----------------------------------------------------------------------------

def get_user_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    profile_button = KeyboardButton('👤 Profile')
    unread_count = sum(1 for n in users.get(str(user_id), {}).get('notifications', []) if not n.get('is_read', False))
    notif_text = '🔔 Notification' + (f' ({unread_count})' if unread_count > 0 else '')
    notification_button = KeyboardButton(notif_text)
    markup.add(profile_button, notification_button)
    return markup

def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton('📊 Statistics'), KeyboardButton('⚙️ Change Bonus'))
    markup.add(KeyboardButton('🔍 Search User'), KeyboardButton('📢 Send Broadcast'))
    markup.add(KeyboardButton('🗑️ Notification All Delete'), KeyboardButton('⬅️ Exit Admin Panel'))
    return markup

def get_admin_user_control_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton('🚫 Block User'), KeyboardButton('✅ Unblock User'))
    markup.add(KeyboardButton('➕ Add Balance'), KeyboardButton('➖ Remove Balance'))
    markup.add(KeyboardButton('✉️ Send Notification'), KeyboardButton('🗑️ Delete Account'))
    markup.add(KeyboardButton('⬅️ Back'))
    return markup

def get_bonus_change_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🪙 Change Coin Bonus"), KeyboardButton("⚡ Change DK Bonus"))
    markup.add(KeyboardButton("⬅️ Back to Admin Panel"))
    return markup

def get_balance_type_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🪙 Coin"), KeyboardButton("⚡ DK"))
    markup.add(KeyboardButton("❌ Cancel"))
    return markup

def get_balance_method_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton('⚡ Immediate Method'), KeyboardButton('🔔 Notification Method'))
    markup.add(KeyboardButton('❌ Cancel'))
    return markup

def get_broadcast_type_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton('✉️ Message All (@all)'), KeyboardButton('🎁 Bonus All (@allbonus)'))
    markup.add(KeyboardButton('⬅️ Back to Admin Panel'))
    return markup

def get_submit_cancel_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton('✅ Submit'), KeyboardButton('❌ Cancel'))
    return markup
    
def get_cancel_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton('❌ Cancel'))
    return markup

# -----------------------------------------------------------------------------
# '/start' কমান্ড হ্যান্ডলার
# -----------------------------------------------------------------------------

@bot.message_handler(commands=['start'])
@block_check_decorator
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name
    
    if user_id not in users or 'custom_id' not in users.get(user_id, {}):
        wc, wd = config.get('welcome_coin_bonus', 300), config.get('welcome_dk_bonus', 50)
        users[user_id] = {'username': username, 'custom_id': generate_unique_id(), 'coin': wc, 'dk': wd, 'blocked': False, 'notifications': []}
        save_user_data(users)
        title, body = "🎉 Welcome to DK CashFlow! 🎉", f"Hello {message.from_user.first_name}!\n\nAs a welcome gift, you received a bonus!\n\n🪙 *Bonus Coins:* {wc}\n⚡ *Bonus DK:* {wd}"
    else:
        users[user_id]['username'] = username
        save_user_data(users)
        title, body = "👋 Welcome Back! 👋", f"Hello again, {message.from_user.first_name}!\nIt's great to see you back."
    bot.send_message(message.chat.id, create_styled_text(title, body), reply_markup=get_user_keyboard(user_id))

# -----------------------------------------------------------------------------
# ইউজার বাটন হ্যান্ডলার (User Button Handlers)
# -----------------------------------------------------------------------------

@bot.message_handler(func=lambda message: message.text == '👤 Profile')
@block_check_decorator
def show_profile(message):
    user_id = str(message.from_user.id)
    if user_id in users:
        ud = users[user_id]
        title = "👤 Your Profile 👤"
        body = (f"🔹 *Username:* @{ud.get('username', 'N/A')}\n"
                f"🆔 *ID Code:* `{ud.get('custom_id', 'N/A')}`\n"
                f"💳 *Telegram ID:* `{user_id}`\n\n"
                "═══════ Balances ═══════\n"
                f"🪙 *Coins:* {ud.get('coin', 0)}\n"
                f"⚡ *DK:* {ud.get('dk', 0)}")
        bot.send_message(message.chat.id, create_styled_text(title, body))
    else:
        bot.send_message(message.chat.id, "❌ Could not find your profile. Press /start first.")

@bot.message_handler(func=lambda message: '🔔 Notification' in message.text)
@block_check_decorator
def user_notifications(message):
    user_id = str(message.from_user.id)
    notifications = users.get(user_id, {}).get('notifications', [])
    if not notifications:
        bot.send_message(message.chat.id, create_styled_text("🔔 Notifications 🔔", "You have no notifications."), reply_markup=get_user_keyboard(user_id)); return
    bot.send_message(message.chat.id, "--- 📬 *Your Notifications* ---")
    for n in notifications: n['is_read'] = True
    save_user_data(users)

    for notif in reversed(notifications):
        title, msg, amount, expiry, is_claimable, b_type = notif.get('title', 'Notification'), notif.get('message', ''), notif.get('amount'), notif.get('expiry_timestamp'), notif.get('is_claimable', False) and not notif.get('claimed', False), notif.get('balance_type', 'coin')
        
        expiry_text = ""
        if expiry: expiry_text = "\n⌛️ *Expired*" if time.time() > expiry else f"\n⏳ *Expires:* {datetime.datetime.fromtimestamp(expiry).strftime('%d %b, %H:%M')}"
        
        bonus_text = ""
        if amount:
            bonus_icon = "🪙" if b_type == 'coin' else "⚡"
            bonus_text = f"\n\n🎁 *Bonus:* {amount} {bonus_icon} {b_type.capitalize()}"

        text = f"*{title}*\n{msg}{bonus_text}{expiry_text}"
        
        markup = InlineKeyboardMarkup()
        buttons = []
        if is_claimable and (not expiry or time.time() < expiry):
            buttons.append(InlineKeyboardButton("✅ Claim Bonus", callback_data=f"claim_{notif['id']}"))
        
        can_delete = not (is_claimable and expiry and time.time() < expiry)
        if can_delete:
            buttons.append(InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_notif_{notif['id']}"))
        
        if buttons: markup.row(*buttons)
        bot.send_message(message.chat.id, text, reply_markup=markup)

    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🗑️ Delete All Read Notifications", callback_data="delete_all_notifs"))
    bot.send_message(message.chat.id, "You can clear all read and expired notifications.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = str(call.from_user.id)
    # কলব্যাক কোয়েরির জন্যও ব্লক চেক করা আবশ্যক
    if user_id in users and users[user_id].get('blocked', False):
        bot.answer_callback_query(call.id, "❌ You are blocked from using the bot.", show_alert=True)
        return

    action, _, value = call.data.partition('_')

    if action == "claim":
        notif = next((n for n in users[user_id].get('notifications', []) if n['id'] == value), None)
        if not notif or notif.get('claimed') or (notif.get('expiry_timestamp') and time.time() > notif.get('expiry_timestamp')):
            bot.answer_callback_query(call.id, "⚠️ Already claimed or expired!")
            if notif: bot.edit_message_text(call.message.text + "\n\n" + ("🎉 *Already Claimed!*" if notif.get('claimed') else "⌛ *Expired!*"), call.message.chat.id, call.message.message_id)
            return

        amount = notif.get('amount', 0)
        balance_type = notif.get('balance_type', 'coin')
        users[user_id][balance_type] = users[user_id].get(balance_type, 0) + amount
        notif['claimed'] = True
        save_user_data(users)
        bot.answer_callback_query(call.id, f"✅ Success! {amount} {balance_type} added.")
        bot.edit_message_text(call.message.text + "\n\n🎉 *Claimed successfully!*", call.message.chat.id, call.message.message_id)

    elif call.data.startswith("delete_notif_"):
        notif = next((n for n in users[user_id]['notifications'] if n['id'] == value), None)
        is_claimable = notif.get('is_claimable', False) and not notif.get('claimed', False) if notif else False
        if is_claimable and notif.get('expiry_timestamp') and time.time() < notif.get('expiry_timestamp'):
            bot.answer_callback_query(call.id, "❌ Cannot delete an active bonus."); return

        users[user_id]['notifications'] = [n for n in users[user_id]['notifications'] if n['id'] != value]
        save_user_data(users)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "🗑️ Notification deleted.")

    elif call.data == "delete_all_notifs":
        users[user_id]['notifications'] = [n for n in users[user_id]['notifications'] if n.get('is_claimable', False) and not n.get('claimed') and n.get('expiry_timestamp') and time.time() < n.get('expiry_timestamp')]
        save_user_data(users)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "🗑️ All deletable notifications cleared.")
        bot.send_message(user_id, "✅ All deletable notifications have been cleared.")

# -----------------------------------------------------------------------------
# অ্যাডমিন প্যানেল হ্যান্ডলার (Admin Panel Handlers)
# -----------------------------------------------------------------------------

@bot.message_handler(func=lambda message: message.text == ADMIN_PASSWORD)
def admin_panel(message):
    bot.send_message(message.chat.id, create_styled_text("👑 Admin Panel 👑", "Welcome, Admin! Choose an option below."), reply_markup=get_admin_keyboard())

# --- মূল অ্যাডমিন বাটন ---
@bot.message_handler(func=lambda message: message.text in ['📊 Statistics', '⚙️ Change Bonus', '⬅️ Exit Admin Panel', '⬅️ Back to Admin Panel', '🔍 Search User', '🗑️ Notification All Delete', '📢 Send Broadcast'])
def main_admin_buttons(message):
    if message.text == '📊 Statistics': show_statistics(message)
    elif message.text == '⚙️ Change Bonus': change_bonus_menu(message)
    elif message.text in ['⬅️ Exit Admin Panel', '⬅️ Back to Admin Panel']: 
        if message.text == '⬅️ Exit Admin Panel': 
            # অ্যাডমিন প্যানেল থেকে বের হওয়ার সময় সাধারণ ইউজার কীবোর্ড দেখানো হয়
            bot.send_message(message.chat.id, "Exiting Admin Panel...", reply_markup=get_user_keyboard(message.from_user.id))
        else: 
            admin_panel(message)
    elif message.text == '🔍 Search User': search_user_prompt(message)
    elif message.text == '🗑️ Notification All Delete': nuke_notifications_prompt(message)
    elif message.text == '📢 Send Broadcast': broadcast_menu(message)

def show_statistics(message):
    valid_users = [u for u in users.values() if isinstance(u, dict)]
    total_coins = sum(u.get('coin', 0) for u in valid_users)
    total_dk = sum(u.get('dk', 0) for u in valid_users)
    title = "📊 Bot Statistics 📊"
    body = (f"👥 *Total Users:* {len(valid_users)}\n"
            f"🪙 *Total Coins:* {total_coins}\n"
            f"⚡ *Total DK:* {total_dk}")
    bot.send_message(message.chat.id, create_styled_text(title, body))

def change_bonus_menu(message):
    cc, cd = config.get('welcome_coin_bonus'), config.get('welcome_dk_bonus')
    title = "⚙️ Bonus Settings ⚙️"
    body = f"Select which bonus to change.\n\n*Current Coin Bonus:* {cc} 🪙\n*Current DK Bonus:* {cd} ⚡"
    bot.send_message(message.chat.id, create_styled_text(title, body), reply_markup=get_bonus_change_keyboard())

@bot.message_handler(func=lambda message: message.text in ["🪙 Change Coin Bonus", "⚡ Change DK Bonus"])
def ask_for_bonus(message):
    bonus_type = "Coin" if "Coin" in message.text else "DK"
    msg = bot.send_message(message.chat.id, f"📝 Please enter the new amount for the *{bonus_type}* welcome bonus.", reply_markup=get_cancel_keyboard())
    bot.register_next_step_handler(msg, set_bonus, bonus_type)

def set_bonus(message, bonus_type):
    if message.text == '❌ Cancel': bot.send_message(message.chat.id, "Operation cancelled.", reply_markup=get_admin_keyboard()); return
    try:
        new_bonus = int(message.text)
        if new_bonus < 0: raise ValueError
        key = 'welcome_coin_bonus' if bonus_type == "Coin" else 'welcome_dk_bonus'
        config[key] = new_bonus
        save_config(config)
        bot.send_message(message.chat.id, f"✅ Success! New {bonus_type} bonus is set to {new_bonus}.", reply_markup=get_admin_keyboard())
    except (ValueError, TypeError):
        bot.send_message(message.chat.id, "❌ Invalid input. Please enter a positive number.", reply_markup=get_admin_keyboard())

def nuke_notifications_prompt(message):
    count = sum(len(u.get('notifications', [])) for u in users.values())
    for u in users.values(): u['notifications'] = []
    save_user_data(users)
    bot.send_message(message.chat.id, create_styled_text("🗑️ Cleanup Complete 🗑️", f"All {count} notifications from all users have been deleted."), reply_markup=get_admin_keyboard())

# --- ইউজার সার্চ এবং কন্ট্রোল ---
def search_user_prompt(message):
    msg = bot.send_message(message.chat.id, create_styled_text("🔍 User Search 🔍", "Enter User ID, Custom ID, or Telegram Username (@username) to search:"), reply_markup=get_cancel_keyboard())
    bot.register_next_step_handler(msg, process_user_search)

def process_user_search(message):
    if message.text == '❌ Cancel': admin_panel(message); return
    user_id, user_data = find_user(message.text)
    if user_id:
        admin_actions[str(message.from_user.id)] = {'target_user_id': user_id}
        body = (f"🔹 *Username:* @{user_data.get('username', 'N/A')}\n"
                f"🆔 *Custom ID:* `{user_data.get('custom_id')}`\n"
                f"💳 *Telegram ID:* `{user_id}`\n"
                f"🪙 *Coins:* {user_data.get('coin', 0)}\n"
                f"⚡ *DK:* {user_data.get('dk', 0)}\n"
                f"🚫 *Blocked:* {'Yes' if user_data.get('blocked') else 'No'}")
        bot.send_message(message.chat.id, create_styled_text("👤 User Found 👤", body), reply_markup=get_admin_user_control_keyboard())
    else:
        bot.send_message(message.chat.id, create_styled_text("⚠️ Search Failed ⚠️", "User not found. Please try again."), reply_markup=get_admin_keyboard())

@bot.message_handler(func=lambda message: message.text in ['🚫 Block User', '✅ Unblock User', '🗑️ Delete Account', '➕ Add Balance', '➖ Remove Balance', '✉️ Send Notification', '⬅️ Back'])
def user_control_handler(message):
    admin_id = str(message.from_user.id)
    if admin_id not in admin_actions or 'target_user_id' not in admin_actions[admin_id]:
        bot.send_message(message.chat.id, "Please search for a user first.", reply_markup=get_admin_keyboard()); return
    
    target_user_id = admin_actions[admin_id]['target_user_id']
    action_map = {'🚫 Block User': ('blocked', True, "blocked"), '✅ Unblock User': ('blocked', False, "unblocked"), '🗑️ Delete Account': (None, None, "deleted"), '⬅️ Back': (None, None, "back")}
    
    if message.text in ['➕ Add Balance', '➖ Remove Balance']:
        admin_actions[admin_id]['balance_action'] = 'add' if '➕' in message.text else 'remove'
        msg = bot.send_message(admin_id, "🪙 Select Balance Type ⚡", reply_markup=get_balance_type_keyboard())
        bot.register_next_step_handler(msg, process_balance_type_selection)
    elif message.text == '✉️ Send Notification':
        msg = bot.send_message(admin_id, "📝 Please enter the notification message for this user:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_single_user_notification)
    elif message.text in action_map:
        key, value, status = action_map[message.text]
        if status == 'back': del admin_actions[admin_id]; admin_panel(message)
        elif status == 'deleted':
            del users[target_user_id]; del admin_actions[admin_id]
            bot.send_message(admin_id, f"🗑️ Account for user `{target_user_id}` has been deleted.", reply_markup=get_admin_keyboard())
        else:
            users[target_user_id][key] = value
            bot.send_message(admin_id, f"✅ User `{target_user_id}` has been {status}.", reply_markup=get_admin_user_control_keyboard())
        save_user_data(users)

# --- ব্যালেন্স কন্ট্রোল ফ্লো ---
def process_balance_type_selection(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_user_control_keyboard()); return
    balance_type = 'dk' if 'DK' in message.text else 'coin'
    admin_actions[admin_id]['balance_type'] = balance_type
    msg = bot.send_message(admin_id, "Choose the method for balance change:", reply_markup=get_balance_method_keyboard())
    bot.register_next_step_handler(msg, process_balance_method)

def process_balance_method(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_user_control_keyboard()); return
    admin_actions[admin_id]['balance_method'] = message.text
    msg = bot.send_message(admin_id, "🔢 Enter the amount:", reply_markup=get_cancel_keyboard())
    bot.register_next_step_handler(msg, process_balance_amount)

def process_balance_amount(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_user_control_keyboard()); return
    try:
        amount = int(message.text)
        if amount <= 0: raise ValueError
        admin_actions[admin_id]['balance_amount'] = amount
        msg = bot.send_message(admin_id, "📝 Enter a title for this transaction (or type 'none'):", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_balance_title)
    except (ValueError, TypeError):
        bot.send_message(admin_id, "❌ Invalid amount. Please enter a positive number.", reply_markup=get_admin_user_control_keyboard())

def process_balance_title(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_user_control_keyboard()); return
    admin_actions[admin_id]['balance_title'] = message.text
    msg = bot.send_message(admin_id, "✍️ Enter a message for this transaction (or type 'none'):", reply_markup=get_cancel_keyboard())
    bot.register_next_step_handler(msg, process_balance_message)

def process_balance_message(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_user_control_keyboard()); return
    admin_actions[admin_id]['balance_message'] = message.text
    if 'Notification' in admin_actions[admin_id].get('balance_method', ''):
        msg = bot.send_message(admin_id, "📅 Enter expiry (e.g., '5 day', '10 minute') or type 'none':", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_balance_expiry)
    else:
        process_balance_expiry(message, skip=True)

def process_balance_expiry(message, skip=False):
    admin_id = str(message.from_user.id)
    if not skip:
        if message.text == '❌ Cancel': bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_user_control_keyboard()); return
        admin_actions[admin_id]['balance_expiry'] = parse_expiry_time(message.text)
    
    data = admin_actions[admin_id]
    action_text = "Add" if data['balance_action'] == 'add' else "Remove"
    balance_icon = "🪙" if data['balance_type'] == 'coin' else "⚡"
    expiry_dt = datetime.datetime.fromtimestamp(data['balance_expiry']).strftime('%d %b %Y, %H:%M') if 'balance_expiry' in data and data['balance_expiry'] else 'None'
    confirm_text = (f"*Action:* {action_text} {data['balance_type'].upper()} {balance_icon}\n"
                    f"*User ID:* `{data['target_user_id']}`\n"
                    f"*Method:* `{data['balance_method']}`\n"
                    f"*Amount:* `{data['balance_amount']}`\n"
                    f"*Title:* `{data['balance_title']}`\n"
                    f"*Expiry:* `{expiry_dt}`")
    msg = bot.send_message(admin_id, create_styled_text("✨ Confirm Action ✨", confirm_text), reply_markup=get_submit_cancel_keyboard())
    bot.register_next_step_handler(msg, final_balance_submit)

def final_balance_submit(message):
    admin_id = str(message.from_user.id)
    if message.text != '✅ Submit': bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_user_control_keyboard()); return

    data = admin_actions[admin_id]
    target_user_id, amount, action, method, b_type = data['target_user_id'], data['balance_amount'], data['balance_action'], data['balance_method'], data['balance_type']
    title = data['balance_title'] if data['balance_title'].lower() != 'none' else f"{action.capitalize()} Balance"
    msg_text = data['message'] if data['message'].lower() != 'none' else f"Admin has {'added' if action == 'add' else 'removed'} {amount} {b_type}."

    if 'Immediate' in method:
        users[target_user_id][b_type] = users[target_user_id].get(b_type, 0) + amount if action == 'add' else max(0, users[target_user_id].get(b_type, 0) - amount)
        bot.send_message(admin_id, f"✅ Success! Balance updated for `{target_user_id}`.", reply_markup=get_admin_user_control_keyboard())
        try: bot.send_message(target_user_id, create_styled_text(f"🔔 {title} 🔔", msg_text))
        except Exception: pass
    else:
        notif = {"id": generate_notification_id(), "title": title, "message": msg_text, "type": "bonus", "amount": amount if action == 'add' else -amount, "balance_type": b_type, "is_claimable": True, "claimed": False, "expiry_timestamp": data.get('balance_expiry'), "created_at": int(time.time()), "is_read": False}
        users[target_user_id].setdefault('notifications', []).append(notif)
        bot.send_message(admin_id, f"✅ Success! Notification sent to `{target_user_id}`.", reply_markup=get_admin_user_control_keyboard())
        try: bot.send_message(target_user_id, "🔔 You have a new notification!")
        except Exception: pass
    
    save_user_data(users)
    del admin_actions[admin_id]

def process_single_user_notification(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_user_control_keyboard()); return
    target_user_id = admin_actions[admin_id]['target_user_id']
    notif = {"id": generate_notification_id(), "title": "✉️ Message from Admin", "message": message.text, "type": "message", "created_at": int(time.time()), "is_read": False}
    users[target_user_id].setdefault('notifications', []).append(notif)
    save_user_data(users)
    bot.send_message(admin_id, f"✅ Notification sent to user `{target_user_id}`.", reply_markup=get_admin_user_control_keyboard())
    try: bot.send_message(target_user_id, f"🔔 You have a new message from the admin!")
    except Exception: pass

# -----------------------------------------------------------------------------
# Global Broadcast System
# -----------------------------------------------------------------------------
def broadcast_menu(message):
    bot.send_message(message.chat.id, create_styled_text("📢 Broadcast Menu 📢", "Select the type of broadcast you want to send."), reply_markup=get_broadcast_type_keyboard())

@bot.message_handler(func=lambda message: message.text in ['✉️ Message All (@all)', '🎁 Bonus All (@allbonus)'])
def handle_broadcast_selection(message):
    if message.text == '✉️ Message All (@all)':
        msg = bot.send_message(message.chat.id, "✍️ Please write the message you want to send to all users:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_broadcast_message)
    elif message.text == '🎁 Bonus All (@allbonus)':
        msg = bot.send_message(message.chat.id, "🪙 Select Balance Type for the bonus ⚡", reply_markup=get_balance_type_keyboard())
        bot.register_next_step_handler(msg, process_broadcast_balance_type)

# --- Broadcast Message Flow ---
def process_broadcast_message(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': admin_panel(message); return
    admin_actions[admin_id] = {'broadcast_type': 'message', 'message': message.text}
    confirm_text = f"You are about to send the following message to ALL users:\n\n`{message.text}`\n\nPlease confirm."
    msg = bot.send_message(admin_id, create_styled_text("✨ Confirm Broadcast ✨", confirm_text), reply_markup=get_submit_cancel_keyboard())
    bot.register_next_step_handler(msg, final_broadcast_submit)

# --- Broadcast Bonus Flow ---
def process_broadcast_balance_type(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': admin_panel(message); return
    balance_type = 'dk' if 'DK' in message.text else 'coin'
    admin_actions[admin_id] = {'broadcast_type': 'bonus', 'balance_type': balance_type}
    msg = bot.send_message(admin_id, f"🔢 Enter the amount for the {balance_type.upper()} bonus:", reply_markup=get_cancel_keyboard())
    bot.register_next_step_handler(msg, process_broadcast_amount)

def process_broadcast_amount(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': admin_panel(message); return
    try:
        amount = int(message.text)
        if amount <= 0: raise ValueError
        admin_actions[admin_id]['amount'] = amount
        msg = bot.send_message(admin_id, "📝 Enter a title for this bonus (or type 'none'):", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_broadcast_title)
    except (ValueError, TypeError):
        bot.send_message(admin_id, "❌ Invalid amount.", reply_markup=get_admin_keyboard())

def process_broadcast_title(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': admin_panel(message); return
    admin_actions[admin_id]['title'] = message.text
    msg = bot.send_message(admin_id, "✍️ Enter a message for this bonus (or type 'none'):", reply_markup=get_cancel_keyboard())
    bot.register_next_step_handler(msg, process_broadcast_bonus_message)

def process_broadcast_bonus_message(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': admin_panel(message); return
    admin_actions[admin_id]['message'] = message.text
    msg = bot.send_message(admin_id, "📅 Enter expiry (e.g., '7 day', '24 hour') or type 'none':", reply_markup=get_cancel_keyboard())
    bot.register_next_step_handler(msg, process_broadcast_expiry)

def process_broadcast_expiry(message):
    admin_id = str(message.from_user.id)
    if message.text == '❌ Cancel': admin_panel(message); return
    admin_actions[admin_id]['expiry'] = parse_expiry_time(message.text)
    
    data = admin_actions[admin_id]
    balance_icon = "🪙" if data['balance_type'] == 'coin' else "⚡"
    expiry_dt = datetime.datetime.fromtimestamp(data['expiry']).strftime('%d %b %Y, %H:%M') if data['expiry'] else 'None'
    confirm_text = (f"*Type:* Bonus for All Users\n"
                    f"*Balance:* {data['balance_type'].upper()} {balance_icon}\n"
                    f"*Amount:* `{data['amount']}`\n"
                    f"*Title:* `{data['title']}`\n"
                    f"*Message:* `{data['message']}`\n"
                    f"*Expiry:* `{expiry_dt}`\n\nPlease confirm.")
    msg = bot.send_message(admin_id, create_styled_text("✨ Confirm Bonus Broadcast ✨", confirm_text), reply_markup=get_submit_cancel_keyboard())
    bot.register_next_step_handler(msg, final_broadcast_submit)

# --- Final Broadcast Submission ---
def final_broadcast_submit(message):
    admin_id = str(message.from_user.id)
    if message.text != '✅ Submit':
        bot.send_message(admin_id, "Operation cancelled.", reply_markup=get_admin_keyboard()); return
    
    data = admin_actions.pop(admin_id, None)
    if not data: return

    if data['broadcast_type'] == 'message':
        notif = {"title": "📢 Broadcast", "message": data['message'], "type": "message"}
        for user_id in users:
            final_notif = {**notif, "id": generate_notification_id(), "created_at": int(time.time()), "is_read": False}
            users[user_id].setdefault('notifications', []).append(final_notif)
            try: bot.send_message(user_id, "📢 You have a new broadcast message from the admin!")
            except Exception: continue
    
    elif data['broadcast_type'] == 'bonus':
        title = data['title'] if data['title'].lower() != 'none' else "🎁 Bonus for Everyone!"
        msg_text = data['message'] if data['message'].lower() != 'none' else f"A special bonus of {data['amount']} {data['balance_type']} is available!"
        notif_template = {"title": title, "message": msg_text, "type": "bonus", "amount": data['amount'], "balance_type": data['balance_type'], "is_claimable": True, "claimed": False, "expiry_timestamp": data.get('expiry')}
        for user_id in users:
            final_notif = {**notif_template, "id": generate_notification_id(), "created_at": int(time.time()), "is_read": False}
            users[user_id].setdefault('notifications', []).append(final_notif)
            try: bot.send_message(user_id, "🎁 You have received a new bonus! Check your notifications.")
            except Exception: continue
            
    save_user_data(users)
    bot.send_message(admin_id, "✅ Broadcast has been sent to all users successfully!", reply_markup=get_admin_keyboard())

# Fallback handler for unknown commands
@bot.message_handler(func=lambda message: True, chat_types=['private'])
@block_check_decorator
def echo_all(message):
    bot.reply_to(message, "Sorry, I don't understand that command. Please use the buttons provided.")

if __name__ == '__main__':
    print("Bot is running...")
    # পুরোনো Middleware সিস্টেমটি পুরোপুরি বাদ দেওয়া হয়েছে।
    bot.infinity_polling()
