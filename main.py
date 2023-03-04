import sqlite3
import datetime
import aiogram
import logging
from aiogram import Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from configs.config import *
from configs.lessons_config import *
from utils.utils import *


db = sqlite3.connect('domashka.db', check_same_thread=False)
c = db.cursor()
#Настройки бота
bot = aiogram.Bot(token, parse_mode='HTML') #токен
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)
print(f" {datetime.datetime.now()} | ДомашкоБот v. 1.0 успешно запущен!")

async def get_dz(call: types.CallbackQuery, name, db_name): # объект CallbackQuery, имя в дательном падеже, запись в БД
    data = c.execute(f"SELECT dz, author, time FROM domashka WHERE predmet = '{db_name}'").fetchone()
    if data is not None:
        if data[0] is None:
            return await bot.answer_callback_query(call.id, f"📔 Домашка по {name} отсутствует!", show_alert=True)
        return await bot.answer_callback_query(call.id, f'\t\t📔 Доска д/з по {name}\n\n😇 Автор: @{data[1]}\n🕓 Время добавления: {data[2]}\n\n📚 Задание:\n{data[0]}', show_alert=True)
    else:
        return await bot.answer_callback_query(call.id, f"📔 Домашка по {name} отсутствует!", show_alert=True)

#///////////////////////////////////////////////////

@dp.message_handler(commands=['start'])
async def start(message):
    data = c.execute(f"SELECT id FROM users WHERE id = {message.from_user.id}").fetchone()
    if data is None:
        c.execute("INSERT INTO users(id, name, surname, dostup) VALUES(?, ?, ?, ?)", (message.from_user.id, message.from_user.first_name, message.from_user.last_name, 0))
        db.commit()
        return await message.reply(f"🎉 Вы успешно зарегистрировались в боте! Ваш ID телеграм - <b>{message.from_user.id}</b>")
    else:
        return await message.reply("🔑 Успешная авторизация!")


@dp.message_handler(commands=['dz'])
async def check_dz(message):
    data = c.execute(f"SELECT dostup FROM users WHERE id = {message.from_user.id}").fetchone()
    if data is None or int(data[0]) < 1:
        return await message.reply("😢 У вас меньше 1 уровня доступа!")
    
    kb = types.InlineKeyboardMarkup()
    for i in lessons:
        kb.add(types.InlineKeyboardButton(text=lessons[i], callback_data=f'check_{i}'))
    
    return await message.reply('🛍 Выберите *школьный предмет* из списка ниже', parse_mode= "Markdown", reply_markup=kb)
        

# Обработка запросов на получение домашки
@dp.callback_query_handler()
async def callback_check_dz(call: types.CallbackQuery):
    if call.from_user.id != call.message.reply_to_message.from_user.id:
        return await bot.answer_callback_query(call.id, f"❗️ Вы не можете использовать чужие сообщения!") 

    if call.data.startswith('check_'):
        lesson_id = call.data.split('check_', maxsplit=1)
        return await get_dz(call, lessons_dat[lesson_id[1]], lesson_id[1])

    #elif call.data == 'return':
    #    kb = types.InlineKeyboardMarkup()
    #    for i in lessons:
    #        kb.add(types.InlineKeyboardButton(text=lessons[i], callback_data=f'check_{i}'))
    #    return await call.message.edit_reply_markup(reply_markup=kb)


@dp.message_handler(commands=['dz_new'])
async def new_dz(message: types.Message):
    user_id = message.from_user.id
    admin_lvl = c.execute(f"SELECT dostup FROM users WHERE id = {user_id}").fetchone()
    if admin_lvl is None or int(admin_lvl[0]) < 2:
        return await message.reply("У вас меньше 2 уровня доступа!")

    info = message.get_args().split(' ', maxsplit=1)
    if len(info) <= 1:
        return await message.reply(f"💻 Для добавления домашки используйте следующий синтакисис:\n<b>/dz_new *предмет* *домашка*</b>\n\nПример:\n<b>/dz_new en1 1. Учебник страница 51 упражнение устно, рабочая тетрадь стр 31 полностью</b>\n\nДоступные предметы:\n<b>{get_text_list_lessons_with_code()}</b>")
    if info[0] not in lessons:
        return await message.reply(f"❗️ Вы указали неверный код предмета!\n\nДоступные предметы:\n{get_text_list_lessons_with_code()}")

    c.execute(f"INSERT INTO logs(user_id, action, result) VALUES({user_id}, 'изменение д/з по {info[0]}', '{info[1]}')")
    db.commit()
    c.execute(f"UPDATE domashka SET dz = '{info[1]}', author = '{message.from_user.username}', time = '{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}' WHERE predmet = '{info[0]}'")
    db.commit()
    await bot.send_message(logs_group, f"🤨 Замечена активность!\n\nID пользователя: <b>{user_id}</b>\nДействие: <b>изменение д/з по {info[0]}</b>\nРезультат: <b>{info[1]}</b>")
    return await message.reply(f"☑️ Вы успешно изменили домашку по <b>{lessons_dat[info[0]]}</b> на:\n\n<b>{info[1]}</b>")


@dp.message_handler(commands=['dz_help'])
async def help_cmd(message: types.Message):
    admin_lvl = c.execute(f"SELECT dostup FROM users WHERE id = {message.from_user.id}").fetchone()
    if admin_lvl is None or int(admin_lvl[0]) < 1:
        return await message.reply("❗️ У вас меньше 1 уровня доступа!")
    
    return await message.reply("😍Команды ДомашкоБота:\n\n<b>/dz</b> - узнать домашнее задание(1+ уровень доступа)\n<b>/dz_help</b> - открыть меню помощи(1+ уровень доступа)\n<b>/dz_new *код предмета* *домашнее задание*</b> - обновить домашнее задание(2+ уровень доступа)\n<b>/dz_clear *код предмета*</b> - очистить домашнее задание(2+ уровень доступа)\n/dz_setadmin *id пользователя* *уровень доступа*")


@dp.message_handler(commands=['dz_clear'])
async def clear_cmd(message: types.Message):
    admin_lvl = c.execute(f"SELECT dostup FROM users WHERE id = {message.from_user.id}").fetchone()
    if admin_lvl is None or int(admin_lvl[0]) < 2:
        return await message.reply("❗️ У вас меньше 2 уровня доступа!")

    info = message.get_args()
    if len(info) <= 2:
        return await message.reply(f"💻 Для обнуления домашки используйте следующий синтакисис:\n<b>/dz_clear предмет</b>\n\nПример:\n<b>/dz_clear en1</b>\n\nДоступные предметы:\n<b>{get_text_list_lessons_with_code()}</b>")
    if info not in lessons:
        return await message.reply(f"❗️ Вы указали неверный код предмета!\n\nДоступные предметы:\n<b>{get_text_list_lessons_with_code()}</b>")

    c.execute(f"UPDATE domashka SET dz = null, author = null, time = null WHERE predmet = '{info}'")
    db.commit()
    c.execute(f"INSERT INTO logs(user_id, action, result) VALUES({message.from_user.id}, 'обнуление {info}', 'успешно')")
    db.commit()
    await bot.send_message(logs_group, f"🤨 Замечена активность!\n\nID пользователя: <b>{message.from_user.id}</b>\nДействие: <b>обнуление {info}</b>\nРезультат: <b>успешно</b>")
    return await message.reply(f"☑️ Вы обнулили домашку по <b>{lessons_dat[info]}</b>")


@dp.message_handler(commands=['dz_setadmin'])
async def clear_cmd(message: types.Message):
    admin_lvl = c.execute(f"SELECT dostup FROM users WHERE id = {message.from_user.id}").fetchone() 
    if int(admin_lvl[0]) < 3 or admin_lvl[0] is None:
        return await message.reply("❗️ У вас меньше 3 уровня доступа!")

    info = message.get_args().split(maxsplit=1)
    if len(info) < 2:
        return await message.reply("❗️ Неверный синтаксис!\n\nИспользуйте: <b>/dz_setadmin id lvl</b>\nПример: <b>/dz_setadmin 1231231234 2</b>")

    data = c.execute(f"SELECT id FROM users WHERE id = {info[0]}").fetchone()
    if data is None:
        return await message.reply("❗️ Пользователь не зарегистрирован в системе бота!")

    try:
        if int(info[1]) > -1 and int(info[1]) <= 3:
            c.execute(f"UPDATE users SET dostup = {info[1]} WHERE id = '{info[0]}'")
            db.commit()
            return await message.reply(f"😁 Вы успешно назначили пользователю с ID <b>{info[0]}</b> доступ уровня <b>{info[1]}</b>!")
        else:
            return await message.reply("❗️ Уровень должен быть больше или равен 0, но меньше или равен 3!")
    except ValueError:
        return await message.reply("❗️ В аргументах команды нельзя использовать буквы!")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)