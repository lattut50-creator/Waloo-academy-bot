import asyncio
import logging
import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ============================================
# SETUP
# ============================================

logging.basicConfig(level=logging.INFO)

# ============================================
# IMPORTANT: PUT YOUR BOT TOKEN HERE!
# ============================================
BOT_TOKEN = "8601191492:AAF0jhimFgfIaodVhAgY9RfpI6hH7d1p3L0"

# ============================================
# YOUR TELEGRAM ID (ADMIN)
# ============================================
ADMIN_ID = 6454146605

# ============================================
# CREATE BOT
# ============================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================
# DATA STORAGE
# ============================================

video_library = {}
questions = {}
users = {}
progress = {}
chat_messages = {}
announcements = {}

DATA_FILE = "waloo_data.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        video_library = data.get('videos', {})
        questions = data.get('questions', {})
        users = data.get('users', {})
        progress = data.get('progress', {})
        chat_messages = data.get('chat_messages', {})
        announcements = data.get('announcements', {})

def save_data():
    data = {
        'videos': video_library,
        'questions': questions,
        'users': users,
        'progress': progress,
        'chat_messages': chat_messages,
        'announcements': announcements
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_lesson_parts(lesson_key):
    parts = []
    for key in video_library.keys():
        if key == lesson_key or key.startswith(lesson_key + "_"):
            parts.append(key)
    parts.sort()
    return parts

def get_next_part(lesson_key, current_part):
    parts = get_lesson_parts(lesson_key)
    if not parts:
        return None
    for i, part in enumerate(parts):
        if part == current_part:
            if i + 1 < len(parts):
                return parts[i + 1]
    return None

def get_previous_part(lesson_key, current_part):
    parts = get_lesson_parts(lesson_key)
    if not parts:
        return None
    for i, part in enumerate(parts):
        if part == current_part:
            if i - 1 >= 0:
                return parts[i - 1]
    return None

def get_part_number(video_key):
    if "_" in video_key:
        parts = video_key.split("_")
        last_part = parts[-1]
        if last_part.isdigit():
            return int(last_part)
    return 1

def get_badges(watched):
    badges = []
    if watched >= 5:
        badges.append("🌟 Beginner")
    if watched >= 10:
        badges.append("📘 Learner")
    if watched >= 20:
        badges.append("📚 Scholar")
    if watched >= 30:
        badges.append("🎓 Economics Expert")
    if watched >= 34:
        badges.append("🏆 Master of Economics")
    return ", ".join(badges) if badges else "No badges yet"

# ============================================
# MENU BAR
# ============================================

def get_student_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 View Units"),
                KeyboardButton(text="📊 My Progress")
            ],
            [
                KeyboardButton(text="❓ Ask Question"),
                KeyboardButton(text="ℹ️ About")
            ],
            [
                KeyboardButton(text="🆘 Help"),
                KeyboardButton(text="🆔 My ID")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Tap a button..."
    )
    return keyboard

def get_admin_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📹 Upload Video"),
                KeyboardButton(text="❓ View Questions")
            ],
            [
                KeyboardButton(text="📢 Send Text"),
                KeyboardButton(text="📊 Dashboard")
            ],
            [
                KeyboardButton(text="🗑️ Delete Content"),
                KeyboardButton(text="🗑️ Delete Announcement")
            ],
            [
                KeyboardButton(text="🔙 Student View")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Admin: Tap a button..."
    )
    return keyboard

# ============================================
# INLINE KEYBOARDS
# ============================================

def get_units_keyboard():
    builder = InlineKeyboardBuilder()
    for unit_id, unit in UNITS.items():
        builder.row(InlineKeyboardButton(
            text=f"📖 {unit['name'][:25]}...",
            callback_data=f"open_unit_{unit_id}"
        ))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"))
    return builder.as_markup()

def get_lessons_keyboard(unit_id):
    builder = InlineKeyboardBuilder()
    unit = UNITS[unit_id]
    for lesson in unit["lessons"]:
        lesson_key = f"{unit_id}_{lesson['id']}"
        parts = get_lesson_parts(lesson_key)
        if parts:
            icon = f"✅ ({len(parts)} parts)"
        else:
            icon = "📹"
        builder.row(InlineKeyboardButton(
            text=f"{icon} {lesson['id']}: {lesson['name']}",
            callback_data=f"view_parts_{lesson_key}"
        ))
    builder.row(InlineKeyboardButton(text="🔙 Back to Units", callback_data="view_units"))
    return builder.as_markup()

def get_parts_keyboard(lesson_key, unit_id):
    builder = InlineKeyboardBuilder()
    parts = get_lesson_parts(lesson_key)
    
    for part in parts:
        part_num = get_part_number(part)
        video_data = video_library[part]
        duration = video_data.get('duration', 0)
        builder.row(InlineKeyboardButton(
            text=f"▶️ Part {part_num} ({duration//60}m {duration%60}s)",
            callback_data=f"play_{part}"
        ))
    
    builder.row(InlineKeyboardButton(text="🔙 Back to Lessons", callback_data=f"open_unit_{unit_id}"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"))
    return builder.as_markup()

def get_video_player_keyboard(video_key, lesson_key, unit_id):
    builder = InlineKeyboardBuilder()
    
    prev_part = get_previous_part(lesson_key, video_key)
    if prev_part:
        builder.row(InlineKeyboardButton(text="⬅️ Previous Part", callback_data=f"play_{prev_part}"))
    
    next_part = get_next_part(lesson_key, video_key)
    if next_part:
        builder.row(InlineKeyboardButton(text="➡️ Next Part", callback_data=f"play_{next_part}"))
    
    builder.row(InlineKeyboardButton(text="📚 All Parts", callback_data=f"view_parts_{lesson_key}"))
    builder.row(InlineKeyboardButton(text="🔙 Back to Lessons", callback_data=f"open_unit_{unit_id}"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"))
    return builder

# ============================================
# COURSE DATA
# ============================================

UNITS = {
    "unit_1": {
        "name": "Unit 1: Fundamental Concepts of Macroeconomics",
        "lessons": [
            {"id": "1.1", "name": "Definition and Focus Areas of Macroeconomics", "duration": "15 min"},
            {"id": "1.2", "name": "Key Challenges in Macroeconomics", "duration": "20 min"},
            {"id": "1.3", "name": "Schools of Thought", "duration": "18 min"}
        ],
        "description": "This unit revisits the definition and focus areas of macroeconomics."
    },
    "unit_2": {
        "name": "Unit 2: Aggregate Demand and Aggregate Supply Analysis",
        "lessons": [
            {"id": "2.1", "name": "Aggregate Demand", "duration": "20 min"},
            {"id": "2.2", "name": "Aggregate Supply", "duration": "18 min"},
            {"id": "2.3", "name": "Equilibrium of AD and AS", "duration": "15 min"}
        ],
        "description": "This unit presents aggregate demand and aggregate supply analysis."
    },
    "unit_3": {
        "name": "Unit 3: Market Failure and Consumer Protection",
        "lessons": [
            {"id": "3.1", "name": "Market Failure", "duration": "15 min"},
            {"id": "3.2", "name": "Public Goods", "duration": "15 min"},
            {"id": "3.3", "name": "Externalities", "duration": "18 min"},
            {"id": "3.4", "name": "Asymmetric Information", "duration": "12 min"},
            {"id": "3.5", "name": "Consumer Protection", "duration": "15 min"}
        ],
        "description": "This unit covers market failure, public goods, externalities, asymmetric information, and consumer protection."
    },
    "unit_4": {
        "name": "Unit 4: Macroeconomic Policy Instruments",
        "lessons": [
            {"id": "4.1", "name": "Definition and Types of Policies", "duration": "12 min"},
            {"id": "4.2", "name": "Fiscal Policy", "duration": "20 min"},
            {"id": "4.3", "name": "Monetary Policy", "duration": "18 min"},
            {"id": "4.4", "name": "Income Policy and Wage", "duration": "15 min"},
            {"id": "4.5", "name": "Foreign Exchange Policies", "duration": "18 min"}
        ],
        "description": "This unit looks at fiscal, monetary, income, and foreign exchange policies."
    },
    "unit_5": {
        "name": "Unit 5: Tax Theory and Practice",
        "lessons": [
            {"id": "5.1", "name": "Taxes: Definition and Principles", "duration": "20 min"},
            {"id": "5.2", "name": "Approaches to Tax Equity", "duration": "12 min"},
            {"id": "5.3", "name": "Tax System in Ethiopia", "duration": "15 min"},
            {"id": "5.4", "name": "Types of Tax in Ethiopia", "duration": "20 min"},
            {"id": "5.5", "name": "Problems of Taxation in Ethiopia", "duration": "12 min"}
        ],
        "description": "This unit explores the concept of taxation in Ethiopia."
    },
    "unit_6": {
        "name": "Unit 6: Poverty and Inequality",
        "lessons": [
            {"id": "6.1", "name": "Concept of Poverty and Its Measurement", "duration": "18 min"},
            {"id": "6.2", "name": "Concept of Inequality", "duration": "15 min"},
            {"id": "6.3", "name": "Global and Regional Poverty", "duration": "12 min"},
            {"id": "6.4", "name": "Women and Poverty", "duration": "15 min"},
            {"id": "6.5", "name": "Poverty and Inequalities in Ethiopia", "duration": "12 min"},
            {"id": "6.6", "name": "Indigenous Knowledge and Poverty", "duration": "12 min"}
        ],
        "description": "This unit focuses on poverty and inequality concepts."
    },
    "unit_7": {
        "name": "Unit 7: Macroeconomic Reforms in Ethiopia",
        "lessons": [
            {"id": "7.1", "name": "National Development Strategies", "duration": "20 min"},
            {"id": "7.2", "name": "Home-grown Economic Reforms", "duration": "18 min"},
            {"id": "7.3", "name": "Fiscal Decentralization", "duration": "15 min"}
        ],
        "description": "This unit presents an overview of macroeconomic reforms in Ethiopia."
    },
    "unit_8": {
        "name": "Unit 8: Economy, Environment and Climate Change",
        "lessons": [
            {"id": "8.1", "name": "Economy and the Environment", "duration": "18 min"},
            {"id": "8.2", "name": "Global Warming and Climate Change", "duration": "20 min"},
            {"id": "8.3", "name": "Green Economy and Green Growth", "duration": "15 min"},
            {"id": "8.4", "name": "Environment and Climate in Ethiopia", "duration": "15 min"}
        ],
        "description": "This unit explores the links between economy, environment, and climate change."
    }
}

TOTAL_LESSONS = sum(len(unit["lessons"]) for unit in UNITS.values())

# ============================================
# START COMMAND
# ============================================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    
    if str(user_id) not in users:
        users[str(user_id)] = {
            'name': user_name,
            'username': message.from_user.username or "No username",
            'joined_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'total_lessons_watched': 0
        }
        progress[str(user_id)] = {}
        save_data()
        print(f"👤 New student: {user_name} (ID: {user_id})")
    
    if user_id == ADMIN_ID:
        text = f"""
👑 **Welcome Admin, {user_name}!**

📊 **Stats:**
• Students: {len(users)}
• Videos: {len(video_library)}
• Questions: {len(questions)}
        """
        await message.answer(text, reply_markup=get_admin_menu(), parse_mode="Markdown")
    else:
        user_progress = progress.get(str(user_id), {})
        watched = len(user_progress)
        text = f"""
🎓 **Welcome to Waloo Academy, {user_name}!** 🎓

📚 **Grade 12 Economics**

📊 **Progress:** {watched}/{TOTAL_LESSONS} lessons ({ (watched / TOTAL_LESSONS * 100) if TOTAL_LESSONS > 0 else 0:.1f}%)

Use the buttons below!
        """
        await message.answer(text, reply_markup=get_student_menu(), parse_mode="Markdown")

# ============================================
# MENU BUTTON HANDLERS
# ============================================

@dp.message(lambda msg: msg.text == "📚 View Units")
async def menu_view_units(message: types.Message):
    await view_units_command(message)

@dp.message(lambda msg: msg.text == "📊 My Progress")
async def menu_my_progress(message: types.Message):
    await progress_command(message)

@dp.message(lambda msg: msg.text == "❓ Ask Question")
async def menu_ask_question(message: types.Message):
    await message.answer(
        "❓ Type: `/ask [your question]`\n\nExample: `/ask What is GDP?`",
        parse_mode="Markdown",
        reply_markup=get_student_menu()
    )

@dp.message(lambda msg: msg.text == "ℹ️ About")
async def menu_about(message: types.Message):
    await about_command(message)

@dp.message(lambda msg: msg.text == "🆘 Help")
async def menu_help(message: types.Message):
    await help_command(message)

@dp.message(lambda msg: msg.text == "🆔 My ID")
async def menu_myid(message: types.Message):
    await show_id_command(message)

# ============================================
# ADMIN MENU HANDLERS
# ============================================

@dp.message(lambda msg: msg.text == "📹 Upload Video")
async def menu_admin_upload(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    await message.answer(
        "📹 **Upload a Video**\n\n"
        "**Format:** `/upload [key] [name]`\n\n"
        "**For multi-part lessons:**\n"
        "`/upload unit_1_1.1_1 Part 1`\n"
        "`/upload unit_1_1.1_2 Part 2`\n\n"
        "**Example:**\n"
        "`/upload unit_1_1.1_1 Definition of Macroeconomics - Part 1`\n"
        "Then attach your video.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu()
    )

@dp.message(lambda msg: msg.text == "❓ View Questions")
async def menu_admin_questions(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    await view_questions_command(message)

@dp.message(lambda msg: msg.text == "📢 Send Text")
async def menu_admin_send_text(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    await message.answer(
        "📢 **Send Announcement**\n\n"
        "Type: `/text [your announcement]`\n\n"
        "**Example:**\n"
        "`/text New video uploaded! Check it out!`\n\n"
        f"📊 Will be sent to all {len(users)} students.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu()
    )

@dp.message(lambda msg: msg.text == "📊 Dashboard")
async def menu_admin_dashboard(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    await dashboard_command(message)

@dp.message(lambda msg: msg.text == "🗑️ Delete Content")
async def menu_admin_delete(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    await delete_content_command(message)

@dp.message(lambda msg: msg.text == "🗑️ Delete Announcement")
async def menu_admin_delete_announcement(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    await message.answer(
        "🗑️ **Delete Announcement**\n\n"
        "Type: `/delete_announcement [announcement text]`\n\n"
        "**Example:**\n"
        "`/delete_announcement New video uploaded!`\n\n"
        "Or type `/list_announcements` to see all announcements.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu()
    )

@dp.message(lambda msg: msg.text == "🔙 Student View")
async def menu_student_view(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    await start_command(message)

# ============================================
# VIEW UNITS
# ============================================

@dp.message(Command("units"))
async def view_units_command(message: types.Message):
    text = "📚 **Grade 12 Economics - All Units**\n\nSelect a unit:"
    await message.answer(text, reply_markup=get_units_keyboard(), parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "view_units")
async def view_units_callback(callback: types.CallbackQuery):
    await callback.answer()
    text = "📚 **Grade 12 Economics - All Units**\n\nSelect a unit:"
    await callback.message.edit_text(text, reply_markup=get_units_keyboard(), parse_mode="Markdown")

# ============================================
# OPEN UNIT
# ============================================

@dp.callback_query(lambda c: c.data.startswith("open_unit_"))
async def open_unit_callback(callback: types.CallbackQuery):
    unit_id = callback.data.replace("open_unit_", "")
    unit = UNITS.get(unit_id)
    
    if not unit:
        await callback.answer("❌ Unit not found!")
        return
    
    await callback.answer()
    
    text = f"""
📖 **{unit['name']}**

📝 {unit['description']}

📹 **Lessons:**
"""
    for lesson in unit["lessons"]:
        lesson_key = f"{unit_id}_{lesson['id']}"
        parts = get_lesson_parts(lesson_key)
        if parts:
            icon = f"✅ ({len(parts)} parts)"
        else:
            icon = "📹"
        text += f"{icon} {lesson['id']}: {lesson['name']}\n"
    
    text += f"\nTotal: {len(unit['lessons'])} lessons"
    text += f"\n✅ = Has video(s) | 📹 = Pending"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_lessons_keyboard(unit_id),
        parse_mode="Markdown"
    )

# ============================================
# VIEW PARTS
# ============================================

@dp.callback_query(lambda c: c.data.startswith("view_parts_"))
async def view_parts_callback(callback: types.CallbackQuery):
    lesson_key = callback.data.replace("view_parts_", "")
    
    unit_id = None
    for u_id, unit in UNITS.items():
        for lesson in unit["lessons"]:
            if f"{u_id}_{lesson['id']}" == lesson_key:
                unit_id = u_id
                break
        if unit_id:
            break
    
    if not unit_id:
        await callback.answer("❌ Lesson not found!")
        return
    
    lesson_name = lesson_key
    for u_id, unit in UNITS.items():
        for lesson in unit["lessons"]:
            if f"{u_id}_{lesson['id']}" == lesson_key:
                lesson_name = lesson['name']
                break
    
    parts = get_lesson_parts(lesson_key)
    
    text = f"""
📹 **{lesson_name}**

📌 This lesson has {len(parts)} part(s):

"""
    for part in parts:
        part_num = get_part_number(part)
        video_data = video_library[part]
        duration = video_data.get('duration', 0)
        text += f"▶️ **Part {part_num}** ({duration//60}m {duration%60}s)\n"
    
    text += f"\nClick a part below to start watching! 📚"
    
    await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=get_parts_keyboard(lesson_key, unit_id),
        parse_mode="Markdown"
    )

# ============================================
# PLAY LESSON
# ============================================

@dp.callback_query(lambda c: c.data.startswith("play_"))
async def play_lesson_callback(callback: types.CallbackQuery):
    video_key = callback.data.replace("play_", "")
    
    if video_key not in video_library:
        await callback.answer("❌ Video not found!")
        return
    
    video_data = video_library[video_key]
    file_id = video_data["file_id"]
    lesson_name = video_data["name"]
    duration = video_data["duration"]
    
    lesson_key = video_key
    if "_" in video_key:
        parts = video_key.split("_")
        if parts[-1].isdigit():
            lesson_key = "_".join(parts[:-1])
    
    unit_id = None
    for u_id, unit in UNITS.items():
        for lesson in unit["lessons"]:
            if f"{u_id}_{lesson['id']}" == lesson_key:
                unit_id = u_id
                break
        if unit_id:
            break
    
    await callback.answer(f"▶️ Playing: {lesson_name}")
    
    user_id = str(callback.from_user.id)
    if user_id not in progress:
        progress[user_id] = {}
    if video_key not in progress[user_id]:
        progress[user_id][video_key] = {
            "watched_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        if user_id in users:
            users[user_id]['total_lessons_watched'] = users[user_id].get('total_lessons_watched', 0) + 1
        save_data()
    
    builder = get_video_player_keyboard(video_key, lesson_key, unit_id)
    
    try:
        await callback.message.answer_video(
            video=file_id,
            caption=f"📹 **{lesson_name}**\n\n"
                   f"⏱️ Duration: {duration//60} minutes {duration%60} seconds\n\n"
                   f"✅ Keep learning! 📚",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.message.delete()
    except Exception as e:
        await callback.message.answer(
            f"❌ Error: {str(e)}\n\nPlease contact admin."
        )

# ============================================
# MAIN MENU CALLBACK
# ============================================

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    try:
        await callback.message.delete()
    except:
        pass
    
    if user_id == ADMIN_ID:
        text = f"👑 **Admin Panel**\n\nStudents: {len(users)}\nVideos: {len(video_library)}\nQuestions: {len(questions)}"
        await callback.message.answer(text, reply_markup=get_admin_menu(), parse_mode="Markdown")
    else:
        user_progress = progress.get(str(user_id), {})
        watched = len(user_progress)
        text = f"🎓 **Welcome back!**\n\nProgress: {watched}/{TOTAL_LESSONS} lessons\n{ (watched / TOTAL_LESSONS * 100) if TOTAL_LESSONS > 0 else 0:.1f}% Complete"
        await callback.message.answer(text, reply_markup=get_student_menu(), parse_mode="Markdown")

# ============================================
# SEND TEXT / ANNOUNCEMENT
# ============================================

@dp.message(Command("text"))
async def send_text_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "📢 `/text [your announcement]`\n\n"
            "**Example:** `/text New video uploaded!`",
            parse_mode="Markdown",
            reply_markup=get_admin_menu()
        )
        return
    
    text_message = parts[1]
    
    # Store announcement
    ann_id = f"ann_{len(announcements) + 1}"
    announcements[ann_id] = {
        "text": text_message,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_data()
    
    sent = 0
    failed = 0
    
    for user_id in users.keys():
        try:
            await bot.send_message(
                chat_id=int(user_id),
                text=f"📢 **Announcement from Waloo Academy**\n\n{text_message}",
                parse_mode="Markdown"
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            print(f"❌ Failed to send to {user_id}: {e}")
    
    await message.answer(f"""
✅ **Announcement Sent!**

📢 {text_message[:100]}{'...' if len(text_message) > 100 else ''}

📤 Sent to: {sent} students
❌ Failed: {failed}

📌 Announcement ID: `{ann_id}`
    """, parse_mode="Markdown", reply_markup=get_admin_menu())

# ============================================
# DELETE ANNOUNCEMENT - METHOD 3
# ============================================

@dp.message(Command("delete_announcement"))
async def delete_announcement_command(message: types.Message):
    """Delete a specific announcement - ADMIN ONLY"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "📝 **Delete Announcement**\n\n"
            "Type: `/delete_announcement [announcement text or ID]`\n\n"
            "**Example:**\n"
            "`/delete_announcement New video uploaded!`\n\n"
            "Or use: `/list_announcements` to see all announcements.",
            parse_mode="Markdown",
            reply_markup=get_admin_menu()
        )
        return
    
    search_text = parts[1]
    
    # Try to find by ID first
    if search_text in announcements:
        del announcements[search_text]
        save_data()
        await message.answer(f"✅ Announcement `{search_text}` deleted!", reply_markup=get_admin_menu())
        return
    
    # Otherwise search by text
    found = None
    for ann_id, ann_data in list(announcements.items()):
        if search_text.lower() in ann_data['text'].lower():
            found = ann_id
            break
    
    if found:
        del announcements[found]
        save_data()
        await message.answer(f"✅ Announcement deleted!", reply_markup=get_admin_menu())
    else:
        await message.answer(
            f"❌ Announcement not found!\n\n"
            f"Type `/list_announcements` to see all announcements.",
            reply_markup=get_admin_menu()
        )

@dp.message(Command("list_announcements"))
async def list_announcements_command(message: types.Message):
    """List all announcements - ADMIN ONLY"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    if not announcements:
        await message.answer("📭 No announcements found.", reply_markup=get_admin_menu())
        return
    
    text = "📢 **All Announcements**\n\n"
    for ann_id, ann_data in list(announcements.items())[:20]:
        text += f"📌 `{ann_id}`\n"
        text += f"   📝 {ann_data['text'][:50]}{'...' if len(ann_data['text']) > 50 else ''}\n"
        text += f"   📅 {ann_data['sent_at']}\n\n"
    
    text += "\nTo delete: `/delete_announcement [announcement_id]`"
    await message.answer(text, parse_mode="Markdown", reply_markup=get_admin_menu())

@dp.message(Command("deleteall_announcements"))
async def delete_all_announcements_command(message: types.Message):
    """Delete ALL announcements - ADMIN ONLY"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    if not announcements:
        await message.answer("📭 No announcements to delete.", reply_markup=get_admin_menu())
        return
    
    count = len(announcements)
    announcements.clear()
    save_data()
    
    await message.answer(f"🗑️ Deleted all {count} announcements!", reply_markup=get_admin_menu())

# ============================================
# ASK QUESTION
# ============================================

@dp.message(Command("ask"))
async def ask_question_command(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❓ `/ask [your question]`\n\nExample: `/ask What is GDP?`",
            parse_mode="Markdown",
            reply_markup=get_student_menu()
        )
        return
    
    question_text = parts[1]
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    question_id = f"q_{len(questions) + 1}"
    
    questions[question_id] = {
        "user_id": user_id,
        "user_name": user_name,
        "question": question_text,
        "asked_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "answered": False
    }
    save_data()
    
    await message.answer(
        f"✅ **Question Sent!**\n\n{question_text}",
        parse_mode="Markdown",
        reply_markup=get_student_menu()
    )
    
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❓ **NEW QUESTION!**\n\n👤 {user_name}\n📝 {question_text}\n\n📌 Reply: /reply {question_id} [answer]",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ Failed to notify admin: {e}")

# ============================================
# REPLY TO QUESTION
# ============================================

@dp.message(Command("reply"))
async def reply_question_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "📝 `/reply [id] [answer]`\n\nExample: `/reply q_1 GDP is...`",
            parse_mode="Markdown",
            reply_markup=get_admin_menu()
        )
        return
    
    question_id = parts[1]
    answer = parts[2]
    
    if question_id not in questions:
        await message.answer(f"❌ Question `{question_id}` not found!")
        return
    
    question_data = questions[question_id]
    student_id = int(question_data["user_id"])
    student_name = question_data["user_name"]
    original_question = question_data["question"]
    
    questions[question_id]["answered"] = True
    questions[question_id]["answer"] = answer
    questions[question_id]["answered_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_data()
    
    try:
        await bot.send_message(
            chat_id=student_id,
            text=f"💬 **Reply from Waloo Academy**\n\n❓ {original_question}\n\n✅ {answer}",
            parse_mode="Markdown",
            reply_markup=get_student_menu()
        )
        await message.answer(f"✅ Reply sent to {student_name}!")
    except Exception as e:
        await message.answer(f"❌ Failed: {str(e)}")

# ============================================
# VIEW QUESTIONS
# ============================================

@dp.message(Command("questions"))
async def view_questions_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    if not questions:
        await message.answer("📭 No questions yet.")
        return
    
    text = "❓ **Student Questions**\n\n"
    for qid, data in list(questions.items())[:20]:
        status = "✅" if data["answered"] else "⏳"
        q_text = data["question"][:40] + "..." if len(data["question"]) > 40 else data["question"]
        text += f"{status} **{qid}** - {data['user_name']}\n   📝 {q_text}\n   📅 {data['asked_at']}\n\n"
    
    text += "\nReply: `/reply [id] [answer]`"
    await message.answer(text, parse_mode="Markdown", reply_markup=get_admin_menu())

# ============================================
# PROGRESS
# ============================================

@dp.message(Command("progress"))
async def progress_command(message: types.Message):
    user_id = str(message.from_user.id)
    user_progress = progress.get(user_id, {})
    watched = len(user_progress)
    
    text = f"""
📊 **Your Progress**

📚 {watched}/{TOTAL_LESSONS} lessons
📈 { (watched / TOTAL_LESSONS * 100) if TOTAL_LESSONS > 0 else 0:.1f}%

⭐ Points: {watched * 10}
🏅 Badges: {get_badges(watched)}
"""
    await message.answer(text, parse_mode="Markdown", reply_markup=get_student_menu())

@dp.callback_query(lambda c: c.data == "my_progress")
async def progress_callback(callback: types.CallbackQuery):
    await callback.answer()
    await progress_command(callback.message)

# ============================================
# DASHBOARD
# ============================================

@dp.message(Command("dashboard"))
async def dashboard_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    total_watched = sum(user.get('total_lessons_watched', 0) for user in users.values())
    text = f"""
👑 **Dashboard**

📊 Students: {len(users)}
📹 Videos: {len(video_library)}
❓ Questions: {len(questions)}
📢 Announcements: {len(announcements)}
👀 Watched: {total_watched}
📅 {datetime.now().strftime("%Y-%m-%d %H:%M")}
    """
    await message.answer(text, parse_mode="Markdown", reply_markup=get_admin_menu())

# ============================================
# DELETE CONTENT
# ============================================

@dp.message(Command("delete"))
async def delete_content_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        if video_library:
            text = "🗑️ **Videos:**\n\n"
            for key, data in video_library.items():
                text += f"• `{key}` - {data['name']}\n"
            text += "\nType: `/delete [key]`"
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("📭 No videos.")
        return
    
    video_key = parts[1]
    if video_key in video_library:
        name = video_library[video_key]['name']
        del video_library[video_key]
        save_data()
        await message.answer(f"🗑️ Deleted: {name}")
    else:
        await message.answer(f"❌ `{video_key}` not found!")

@dp.message(Command("deleteall"))
async def delete_all_videos(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    if not video_library:
        await message.answer("📭 No videos to delete.")
        return
    
    count = len(video_library)
    video_library.clear()
    save_data()
    
    await message.answer(f"🗑️ Deleted all {count} videos!")

# ============================================
# UPLOAD VIDEO
# ============================================

@dp.message(Command("upload"))
async def upload_video_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    if not message.video:
        await message.answer(
            "📹 **Upload a Video**\n\n"
            "**Format:** `/upload [key] [name]`\n\n"
            "**For multi-part lessons:**\n"
            "`/upload unit_1_1.1_1 Part 1`\n"
            "`/upload unit_1_1.1_2 Part 2`\n\n"
            "**Example:**\n"
            "`/upload unit_1_1.1_1 Definition of Macroeconomics - Part 1`\n"
            "Then attach your video.",
            parse_mode="Markdown"
        )
        return
    
    caption = message.caption or ""
    parts = caption.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.answer(
            "❌ **Format:** `/upload [key] [name]`\n\n"
            "Example: `/upload unit_1_1.1_1 Definition of Macroeconomics - Part 1`",
            parse_mode="Markdown"
        )
        return
    
    video_key = parts[1]
    lesson_name = parts[2]
    
    video = message.video
    file_id = video.file_id
    duration = video.duration
    file_size = video.file_size
    
    video_library[video_key] = {
        "name": lesson_name,
        "file_id": file_id,
        "duration": duration,
        "size": file_size,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    save_data()
    
    await message.answer(f"""
✅ **Video Uploaded!**

📹 {lesson_name}
📌 `{video_key}`
⏱️ {duration//60}m {duration%60}s
📦 {file_size//1024}KB

🎯 Students can now view this lesson!
    """, parse_mode="Markdown")

# ============================================
# STUDENTS LIST
# ============================================

@dp.message(Command("students"))
async def view_students_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access Denied!")
        return
    
    if not users:
        await message.answer("👥 No students yet.")
        return
    
    text = "👥 **Students**\n\n"
    for i, (uid, data) in enumerate(users.items(), 1):
        watched = progress.get(uid, {})
        text += f"{i}. **{data['name']}**\n"
        text += f"   🆔 `{uid}`\n"
        text += f"   📚 {len(watched)} lessons\n"
        text += f"   📅 {data['joined_at']}\n\n"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=get_admin_menu())

# ============================================
# HELP, ABOUT, MYID
# ============================================

@dp.message(Command("help"))
async def help_command(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = """
👑 **Admin Commands**

📹 /upload - Upload video
📢 /text - Send announcement
❓ /questions - View questions
💬 /reply - Reply to question
🗑️ /delete - Delete content
🗑️ /deleteall - Delete all videos
🗑️ /delete_announcement - Delete announcement
📋 /list_announcements - List announcements
📊 /dashboard - View stats
👥 /students - View students
        """
    else:
        text = """
🤖 **Student Commands**

/start - Start the bot
/units - View all units
/ask - Ask a question
/progress - View progress
/myid - Show your ID
/about - About Academy
/help - This menu
        """
    await message.answer(text, parse_mode="Markdown", reply_markup=get_student_menu() if message.from_user.id != ADMIN_ID else get_admin_menu())

@dp.message(Command("about"))
async def about_command(message: types.Message):
    text = "🏛️ **Waloo Academy**\n\n📚 Grade 12 Economics\n📖 8 Units | 34 Lessons\n🎯 Making quality education accessible!"
    await message.answer(text, parse_mode="Markdown", reply_markup=get_student_menu() if message.from_user.id != ADMIN_ID else get_admin_menu())

@dp.message(Command("myid"))
async def show_id_command(message: types.Message):
    await message.answer(f"🆔 **Your ID:** `{message.from_user.id}`", parse_mode="Markdown", reply_markup=get_student_menu() if message.from_user.id != ADMIN_ID else get_admin_menu())

# ============================================
# MESSAGE HANDLER
# ============================================

@dp.message()
async def handle_other_messages(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {'name': message.from_user.first_name, 'username': message.from_user.username or "No username", 'joined_at': datetime.now().strftime("%Y-%m-%d %H:%M"), 'total_lessons_watched': 0}
        progress[user_id] = {}
        save_data()
    
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Use buttons below:", reply_markup=get_admin_menu())
    else:
        await message.answer("🤔 Use buttons or type /help", reply_markup=get_student_menu())

# ============================================
# START BOT
# ============================================

async def main():
    print("=" * 60)
    print("🚀 WALOO ACADEMY BOT - WITH DELETE FEATURES")
    print("=" * 60)
    print(f"📱 Bot online!")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"👥 Students: {len(users)}")
    print(f"📹 Videos: {len(video_library)}")
    print(f"📢 Announcements: {len(announcements)}")
    print(f"❓ Questions: {len(questions)}")
    print("=" * 60)
    print("✅ Includes announcement delete features!")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
