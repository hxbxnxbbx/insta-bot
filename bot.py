import os
import json
import random
import time
import threading
import requests
import yt_dlp
from telebot import TeleBot, types
from instagrapi import Client

TOKEN = "8836481861:AAG1b3-AqM0o4P2AAq7FSFLnQ0j3KepEjCM"
bot = TeleBot(TOKEN)

DATA_FILE = "users_accounts.json"
SECRET_PASS = "hamza2005"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_states = {}
user_temp_data = {}

def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📤 نشر ريلز تلقائي"),
        types.KeyboardButton("🎬 نشر ستوري"),
        types.KeyboardButton("👥 متابعة حسابات"),
        types.KeyboardButton("⚙️ إدارة الحسابات"),
        types.KeyboardButton("🟢/🔴 تفعيل وإطفاء الحسابات"),
        types.KeyboardButton("⚙️ تعيين كابشن وغلاف")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    data = load_data()
    
    if chat_id in data and data[chat_id].get("authorized", False):
        user_states[chat_id] = "normal"
        bot.send_message(
            chat_id,
            "أهلاً بك مجدداً يا حمزة في لوحة تحكم وإدارة حسابات إنستغرام 🎬",
            reply_markup=main_menu(message.chat.id)
        )
    else:
        user_states[chat_id] = "waiting_for_password"
        bot.send_message(
            chat_id,
            "🔒 **مرحباً بك! هذا البوت محمي.**\n\nالرجاء إرسال **رمز المرور** لفتح البوت واستخدامه لأول مرة:"
        )

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_password")
def check_password(message):
    chat_id = str(message.chat.id)
    entered_pass = message.text.strip()
    
    if entered_pass == SECRET_PASS:
        data = load_data()
        if chat_id not in data:
            data[chat_id] = {}
        data[chat_id]["authorized"] = True
        save_data(data)
        
        user_states[chat_id] = "normal"
        bot.send_message(
            chat_id,
            "✅ **تم التحقق بنجاح! تم فتح البوت لك للأبد.**\n\nاختر ما تريد من الأزرار أدناه للبدء:",
            reply_markup=main_menu(message.chat.id)
        )
    else:
        bot.send_message(
            chat_id,
            "❌ **الرمز غير صحيح!**\nيرجى إرسال الرمز الصحيح لكي يعمل البوت:"
        )

@bot.message_handler(func=lambda msg: msg.text in [
    "📤 نشر ريلز تلقائي", "🎬 نشر ستوري", "👥 متابعة حسابات", 
    "⚙️ إدارة الحسابات", "🟢/🔴 تفعيل وإطفاء الحسابات", "⚙️ تعيين كابشن وغلاف"
])
def handle_main_buttons(message):
    chat_id = str(message.chat.id)
    data = load_data()
    
    if not data.get(chat_id, {}).get("authorized", False):
        user_states[chat_id] = "waiting_for_password"
        bot.send_message(chat_id, "🔒 يرجى إدخال رمز المرور أولاً:")
        return

    text = message.text
    
    if text == "⚙️ إدارة الحسابات":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ إضافة حساب جديد", callback_data="add_account"))
        markup.add(types.InlineKeyboardButton("🗑️ حذف حساب", callback_data="delete_account"))
        bot.send_message(chat_id, "⚙️ **قسم إدارة الحسابات:**\nاختر العملية التي تريدها:", reply_markup=markup)
        
    elif text == "🟢/🔴 تفعيل وإطفاء الحسابات":
        show_toggle_menu(chat_id, message.message_id)
        
    elif text == "⚙️ تعيين كابشن وغلاف":
        user_states[chat_id] = "waiting_for_preset_caption"
        bot.send_message(chat_id, "✍️ أرسل الآن **الكابشن الثابت** الذي تريد استخدامه لكل الريلز القادمة:")
        
    elif text == "📤 نشر ريلز تلقائي":
        active_accs = get_active_accounts_dict(chat_id)
        if not active_accs:
            bot.send_message(chat_id, "⚠️ ليس لديك أي حساب **مفعل (ON)** حالياً للنشر.")
            return
        
        markup = types.InlineKeyboardMarkup()
        for nick in active_accs.keys():
            markup.add(types.InlineKeyboardButton(f"👤 حساب: {nick}", callback_data=f"auto_acc_{nick}"))
        bot.send_message(chat_id, "🎯 **اختر الحساب الذي تريد النشر به:**", reply_markup=markup)

    elif text == "🎬 نشر ستوري":
        if not get_active_accounts(chat_id):
            bot.send_message(chat_id, "⚠️ ليس لديك أي حساب **مفعل (ON)** حالياً لنشر الستوري.")
            return
        user_states[chat_id] = "waiting_for_story_link"
        bot.send_message(chat_id, "🔗 أرسل الآن رابط الفيديو (من تيك توك أو انستغرام) لنشره كـ **ستوري**:")
        
    elif text == "👥 متابعة حسابات":
        if not get_active_accounts(chat_id):
            bot.send_message(chat_id, "⚠️ ليس لديك أي حساب **مفعل (ON)** للمتابعة.")
            return
        user_states[chat_id] = "waiting_for_follow_user"
        bot.send_message(chat_id, "👤 أرسل الآن **يوزر (Username)** الحساب الذي تريد متابعته بالحسابات المُفعلة:")

@bot.callback_query_handler(func=lambda call: call.data.startswith("auto_acc_"))
def select_auto_account(call):
    chat_id = str(call.message.chat.id)
    nick = call.data.replace("auto_acc_", "")
    bot.answer_callback_query(call.id)
    
    if chat_id not in user_temp_data: user_temp_data[chat_id] = {}
    user_temp_data[chat_id]["auto_target_account"] = nick
    user_states[chat_id] = "waiting_for_auto_count"
    
    bot.edit_message_text(
        f"✅ تم اختيار الحساب: **{nick}**\n\n🔢 الآن أرسل **عدد الريلزات** التي تريد نشرها (مثلاً: `10`):",
        chat_id,
        call.message.message_id
    )

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_auto_count")
def get_auto_count(message):
    chat_id = str(message.chat.id)
    try:
        count = int(message.text.strip())
        if count <= 0: raise ValueError()
    except:
        bot.send_message(chat_id, "⚠️ يرجى إرسال رقم صحيح وموجب لعدد الفيديوهات:")
        return
        
    if chat_id not in user_temp_data: user_temp_data[chat_id] = {}
    user_temp_data[chat_id]["auto_count"] = count
    user_states[chat_id] = "waiting_for_auto_links"
    
    bot.send_message(
        chat_id,
        f"🔗 ممتاز! الآن أرسل **({count}) رابط فيديو** بحيث يكون كل رابط في سطر منفصل:"
    )

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_auto_links")
def get_auto_links(message):
    chat_id = str(message.chat.id)
    links = [l.strip() for l in message.text.split("\n") if l.strip()]
    
    if len(links) == 0:
        bot.send_message(chat_id, "⚠️ لم تقم بإرسال أي روابط. أعد المحاولة:")
        return
        
    if chat_id not in user_temp_data: user_temp_data[chat_id] = {}
    user_temp_data[chat_id]["auto_links"] = links
    user_states[chat_id] = "waiting_for_auto_interval"
    
    bot.send_message(
        chat_id,
        f"⏱️ تم استلام ({len(links)}) رابط بنجاح.\n\nالآن أرسل **الفاصل الزمني بالدقائق** بين كل ريل والآخر (مثلاً اكتب هكذا: `90-100` أو ارسل رقماً ثابتاً مثل `90`):"
    )

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_auto_interval")
def get_auto_interval(message):
    chat_id = str(message.chat.id)
    text = message.text.strip()
    
    try:
        if "-" in text:
            parts = text.split("-")
            min_m = int(parts[0].strip())
            max_m = int(parts[1].strip())
            interval_range = (min_m, max_m)
        else:
            val = int(text)
            interval_range = (val, val)
    except:
        bot.send_message(chat_id, "⚠️ صيغة الوقت غير صحيحة. يرجى الإرسال بصيغة صحيحة مثل `90-100` أو `60`:")
        return
        
    data_temp = user_temp_data.get(chat_id, {})
    links = data_temp.get("auto_links", [])
    target_nick = data_temp.get("auto_target_account")
    
    user_states[chat_id] = "normal"
    bot.send_message(
        chat_id,
        f"🚀 **تم بدء نظام النشر التسلسلي بنجاح!**\n- الحساب: `{target_nick}`\n- إجمالي الروابط: `{len(links)}`\n- الفاصل الزمني: `{text} دقيقة` (سيتم نشر أول ريل فوراً، ثم الانتظار بين كل ريل والذي يليه).",
        reply_markup=main_menu(message.chat.id)
    )
    
    threading.Thread(target=run_sequential_auto_upload, args=(chat_id, target_nick, links, interval_range)).start()

def run_sequential_auto_upload(chat_id, target_nick, links, interval_range):
    data = load_data()
    user_info = data.get(chat_id, {})
    accounts = user_info.get("accounts", {})
    
    if target_nick not in accounts:
        bot.send_message(chat_id, f"❌ حدث خطأ: الحساب `{target_nick}` غير موجود.")
        return
        
    session_id = accounts[target_nick]["session_id"]
    caption = user_info.get("preset_caption", "Reels")
    cover_path = user_info.get("preset_cover", "")
    
    current_links = list(links)
    total_links_count = len(current_links)
    
    index = 1
    while current_links:
        link = current_links.pop(0)
        bot.send_message(chat_id, f"⏳ جاري تحميل ونشر الريل رقم ({index}/{total_links_count}) من الرابط:\n`{link}`", parse_mode="Markdown")
        
        video_path = download_best_video(link, chat_id)
        
        if video_path and os.path.exists(video_path):
            try:
                cl = Client()
                cl.login_by_sessionid(session_id)
                if cover_path and os.path.exists(cover_path):
                    cl.clip_upload(path=video_path, caption=caption, thumbnail=cover_path)
                else:
                    cl.clip_upload(path=video_path, caption=caption)
                bot.send_message(chat_id, f"✅ تم نشر الريل ({index}) بنجاح على حساب `{target_nick}`.")
            except Exception as e:
                bot.send_message(chat_id, f"❌ فشل النشر على إنستغرام للرابط ({index}): {e}")
            os.remove(video_path)
        else:
            bot.send_message(chat_id, f"❌ فشل تحميل الفيديو للرابط ({index}), سيتم تخطيه.")
            
        index += 1
        
        # إذا كانت هناك روابط متبقية، انتظر الوقت المحدد قبل الانتقال للريل التالي
        if current_links:
            wait_minutes = random.randint(interval_range[0], interval_range[1])
            bot.send_message(chat_id, f"⏱️ تم الانتهاء من نشر الريل الحالي. متبقي ({len(current_links)}) روابط. سيتم الانتظار لمدة `{wait_minutes} دقيقة` لنشر الريل القادم...")
            time.sleep(wait_minutes * 60)
            
    bot.send_message(chat_id, f"حساب {target_nick} تم نشر بالكامل")

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_preset_caption")
def get_preset_caption(message):
    chat_id = str(message.chat.id)
    caption = message.text.strip()
    if chat_id not in user_temp_data: user_temp_data[chat_id] = {}
    user_temp_data[chat_id]["preset_caption"] = caption
    user_states[chat_id] = "waiting_for_preset_cover"
    bot.send_message(chat_id, "🖼️ ممتاز! أرسل الآن **صورة الغلاف الثابتة** بجودة عالية:")

@bot.message_handler(content_types=['photo'], func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_preset_cover")
def get_preset_cover(message):
    chat_id = str(message.chat.id)
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    cover_path = f"preset_cover_{chat_id}.jpg"
    with open(cover_path, 'wb') as f:
        f.write(downloaded_file)
        
    preset_caption = user_temp_data.get(chat_id, {}).get("preset_caption", "")
    data = load_data()
    if chat_id not in data: data[chat_id] = {}
    
    data[chat_id]["preset_caption"] = preset_caption
    data[chat_id]["preset_cover"] = cover_path
    save_data(data)
    
    user_states[chat_id] = "normal"
    bot.send_message(chat_id, "✅ **تم حفظ الكابشن والغلاف الثابت بنجاح!**", reply_markup=main_menu(message.chat.id))

@bot.callback_query_handler(func=lambda call: call.data in ["add_account", "delete_account"])
def account_management_callback(call):
    chat_id = str(call.message.chat.id)
    if call.data == "add_account":
        user_states[chat_id] = "waiting_for_session_id"
        bot.send_message(chat_id, "🔑 أرسل الآن **Session ID** الخاص بالحساب الجديد:")
    elif call.data == "delete_account":
        data = load_data()
        user_accs = get_accounts_dict(chat_id, data)
        if not user_accs:
            bot.answer_callback_query(call.id, "لا توجد حسابات مضافة للحذف!")
            return
        markup = types.InlineKeyboardMarkup()
        for nick, info in user_accs.items():
            markup.add(types.InlineKeyboardButton(f"🗑️ حذف: {nick}", callback_data=f"del_{nick}"))
        bot.send_message(chat_id, "🗑️ اختر الحساب الذي ترغب بحذفه:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def confirm_delete_account(call):
    chat_id = str(call.message.chat.id)
    nick = call.data.replace("del_", "")
    data = load_data()
    if chat_id in data and "accounts" in data[chat_id]:
        if nick in data[chat_id]["accounts"]:
            del data[chat_id]["accounts"][nick]
            save_data(data)
            bot.answer_callback_query(call.id, f"تم حذف الحساب ({nick}) بنجاح!")
            bot.edit_message_text("✅ تم حذف الحساب بنجاح.", chat_id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_session_id")
def receive_session_id(message):
    chat_id = str(message.chat.id)
    user_temp_data[chat_id] = {"session_id": message.text.strip()}
    user_states[chat_id] = "waiting_for_nickname"
    bot.send_message(chat_id, "🏷️ أرسل الآن **اسم وهمي** لتمييز هذا الحساب:")

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_nickname")
def receive_nickname(message):
    chat_id = str(message.chat.id)
    nick = message.text.strip()
    session_id = user_temp_data.get(chat_id, {}).get("session_id")
    
    data = load_data()
    if chat_id not in data: data[chat_id] = {}
    if "accounts" not in data[chat_id]: data[chat_id]["accounts"] = {}
    
    if nick in data[chat_id]["accounts"]:
        bot.send_message(chat_id, "⚠️ هذا الاسم موجود مسبقاً، أرسل اسم آخر:")
        return
        
    data[chat_id]["accounts"][nick] = {"session_id": session_id, "status": "on"}
    save_data(data)
    user_states[chat_id] = "normal"
    bot.send_message(chat_id, f"✅ تم إضافة الحساب باسم (**{nick}**) وتفعيله!", reply_markup=main_menu(message.chat.id))

def get_accounts_dict(chat_id, data=None):
    if not data: data = load_data()
    u_data = data.get(chat_id, {})
    return u_data.get("accounts", {})

def show_toggle_menu(chat_id, message_id=None):
    user_accs = get_accounts_dict(chat_id)
    if not user_accs:
        bot.send_message(chat_id, "⚠️ لا توجد حسابات مضافة حالياً.")
        return
    markup = types.InlineKeyboardMarkup()
    for nick, info in user_accs.items():
        state_icon = "🟢 ON" if info["status"] == "on" else "🔴 OFF"
        markup.add(types.InlineKeyboardButton(f"{nick} ➔ {state_icon}", callback_data=f"toggle_{nick}"))
    text = "🟢/🔴 **لوحة التحكم بالحسابات:**"
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
            return
        except:
            pass
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def toggle_account_status(call):
    chat_id = str(call.message.chat.id)
    nick = call.data.replace("toggle_", "")
    data = load_data()
    user_accs = get_accounts_dict(chat_id, data)
    if nick in user_accs:
        current_status = user_accs[nick]["status"]
        user_accs[nick]["status"] = "off" if current_status == "on" else "on"
        data[chat_id]["accounts"] = user_accs
        save_data(data)
        show_toggle_menu(chat_id, call.message.message_id)

def get_active_accounts_dict(chat_id):
    user_accs = get_accounts_dict(chat_id)
    return {nick: info["session_id"] for nick, info in user_accs.items() if info["status"] == "on"}

def get_active_accounts(chat_id):
    return len(get_active_accounts_dict(chat_id)) > 0

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_story_link")
def get_story_link(message):
    chat_id = str(message.chat.id)
    video_url = message.text.strip()
    user_states[chat_id] = "normal"
    bot.send_message(chat_id, "⏳ جاري نشر الستوري...")
    active_accs = get_active_accounts_dict(chat_id)
    video_path = download_best_video(video_url, chat_id)
    
    if not video_path or not os.path.exists(video_path):
        bot.send_message(chat_id, "❌ فشل تحميل الفيديو.", reply_markup=main_menu(message.chat.id))
        return
        
    success_count = 0
    for nick, session_id in active_accs.items():
        try:
            cl = Client()
            cl.login_by_sessionid(session_id)
            cl.video_upload_to_story(video_path)
            success_count += 1
        except Exception as e:
            print(f"Story Error {nick}: {e}")
            
    if os.path.exists(video_path): os.remove(video_path)
    bot.send_message(chat_id, f"✅ تم نشر الستوري على ({success_count}) حساب!", reply_markup=main_menu(message.chat.id))

@bot.message_handler(func=lambda msg: user_states.get(str(msg.chat.id)) == "waiting_for_follow_user")
def execute_follow(message):
    chat_id = str(message.chat.id)
    target_username = message.text.strip().replace("@", "")
    user_states[chat_id] = "normal"
    bot.send_message(chat_id, f"⏳ جاري المتابعة (@{target_username})...")
    active_accs = get_active_accounts_dict(chat_id)
    
    success_count = 0
    for nick, session_id in active_accs.items():
        try:
            cl = Client()
            cl.login_by_sessionid(session_id)
            user_id = cl.user_id_from_username(target_username)
            cl.user_follow(user_id)
            success_count += 1
        except Exception as e:
            print(f"Follow Error {nick}: {e}")
            
    bot.send_message(chat_id, f"✅ تمت المتابعة بنجاح باستخدام ({success_count}) حساب!", reply_markup=main_menu(message.chat.id))

def download_best_video(url, chat_id):
    v_path = f"video_{chat_id}_{random.randint(1000,9999)}.mp4"
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': v_path,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(v_path) and os.path.getsize(v_path) > 0:
            return v_path
    except Exception:
        pass

    if "tiktok.com" in url:
        try:
            api_url = f"https://tikwm.com/api/?url={url}&hd=1"
            response = requests.get(api_url).json()
            if "data" in response and ("play" in response["data"] or "hdplay" in response["data"]):
                video_link = response["data"].get("hdplay") or response["data"]["play"]
                video_content = requests.get(video_link).content
                with open(v_path, "wb") as f:
                    f.write(video_content)
                if os.path.exists(v_path) and os.path.getsize(v_path) > 0:
                    return v_path
        except Exception:
            pass
        
    return None

if __name__ == "__main__":
    print("Bot is running successfully with sequential upload...")
    bot.infinity_polling(skip_pending=True)
EOF
