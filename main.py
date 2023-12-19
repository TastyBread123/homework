import sqlite3, logging

from asyncio import run
from datetime import datetime

from aiogram import Dispatcher, types, Bot, Router, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.markdown import hlink

from database import Database
from configs.config import token, logs_group, anti_group_dz
from configs.lessons_config import lessons
from utils.utils import get_text_list_lessons_with_code

#Настройки бота
bot = Bot(token, parse_mode='HTML')
dp = Dispatcher(disable_fsm=True)
router = Router()
logging.basicConfig(level=logging.INFO)
db = Database('domashka.db')


# Обработка запросов на получение домашки
@router.callback_query(F.data.startswith('check_'))
async def callback_check_dz(call: types.CallbackQuery):
    dostup = await db.get_user_dostup(call.from_user.id)
    if dostup is None or dostup < 1: return await call.answer("😢 У вас нет 1 уровня доступа!")

    lesson_code = call.data.split('_', maxsplit=1)[1]    
    data = await db.get_dz(lesson_code)

    if data is None or data[0] is None: return await call.answer(f"📔 Домашка по {lessons[lesson_code][1]} отсутствует!", show_alert=True)    
    await call.message.answer(f'📔 Доска д/з по {lessons[lesson_code][1]}\n🕓 Время добавления: {data[2]} ({hlink("автор", data[1])})\n\n📚 Задание:\n{data[0]}', parse_mode='HTML')
    return call.answer()

#///////////////////////////////////////////////////

@dp.message(Command('start'))
async def start(message: types.Message):
    registration = await db.add_user((message.from_user.id, message.from_user.first_name, message.from_user.last_name))
    
    if registration == 'Error': return print('ОШИБКА В ЗАПРОСЕ!!!!')
    if not registration: return await message.reply(f"🔑 Успешная авторизация! Здравствуйте, {message.from_user.first_name}")
    return await message.reply(f"🎉 Вы успешно зарегистрировались в боте! Ваш ID телеграм - <b>{message.from_user.id}</b>")


@dp.message(Command('dz'))
async def check_dz(message: types.Message):
    dostup = await db.get_user_dostup(message.from_user.id)
    if dostup is None or dostup < 1: return await message.reply("😢 У вас нет 1 уровня доступа!")
    if message.chat.id < 0 and anti_group_dz: return await message.reply("😢 В целях анти-флуда данную команду <b>НЕЛЬЗЯ</b> использовать в группах!\nПожалуйста, используйте ее в личке с ботом")
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard = [[types.InlineKeyboardButton(text=lessons[i][0], callback_data=f'check_{i}')] for i in lessons])
    return await message.reply('🛍 Выберите *школьный предмет* из списка ниже', parse_mode= "Markdown", reply_markup=keyboard)


@dp.message(Command('dz_new'))
async def new_dz(message: types.Message, command: CommandObject):
    dostup = await db.get_user_dostup(message.from_user.id)
    if dostup is None or dostup < 2: return await message.reply("😢 У вас нет 2 уровня доступа!")

    if command.args is None: return await message.reply(f"💻 Для добавления домашки используйте следующий синтакисис:\n<b>/dz_new *предмет* *домашка*</b>\n\nПример:\n<b>/dz_new en1 1. Учебник страница 51 упражнение устно, рабочая тетрадь стр 31 полностью</b>\n\nДоступные предметы:\n<b>{get_text_list_lessons_with_code()}</b>")
    info = command.args.split(' ', maxsplit=1)
    if len(info) < 2: return await message.reply(f"💻 Для добавления домашки используйте следующий синтакисис:\n<b>/dz_new *предмет* *домашка*</b>\n\nПример:\n<b>/dz_new en1 1. Учебник страница 51 упражнение устно, рабочая тетрадь стр 31 полностью</b>\n\nДоступные предметы:\n<b>{get_text_list_lessons_with_code()}</b>")
    if info[0] not in lessons: return await message.reply(f"❗️ Вы указали неверный код предмета!\n\nДоступные предметы:\n{get_text_list_lessons_with_code()}")
    
    await db.add_new_dz(message.from_user.id, message.from_user.url, info[0], info[1])
    await message.reply(f"☑️ Вы успешно изменили домашку по <b>{lessons[info[0]][1]}</b> на:\n\n<b>{info[1]}</b>")
    return await bot.send_message(logs_group, f"🤨 Пользователь: {hlink(message.from_user.first_name, message.from_user.url)}\nДействие: <b>изменение домашки по {lessons[info[0]][1]}</b>\nНовая домашка: <b>{info[1]}</b>")


@dp.message(Command('help'))
async def help_cmd(message: types.Message):
    dostup = await db.get_user_dostup(message.from_user.id)
    if dostup is None or dostup < 1: return await message.reply("😢 У вас нет 1 уровня доступа!")
    return await message.reply("😍Команды ДомашкоБота:\n\n<b>/dz</b> - узнать домашнее задание (1+ уровень доступа)\n<b>/dz_help</b> - открыть меню помощи (1+ уровень доступа)\n<b>/dz_new *код предмета* *домашнее задание*</b> - обновить домашнее задание (2+ уровень доступа)\n<b>/dz_clear *код предмета*</b> - очистить домашнее задание (2+ уровень доступа)\n/dz_setadmin *id пользователя* *уровень доступа*")


@dp.message(Command('dz_clear'))
async def clear_cmd(message: types.Message, command: CommandObject):
    dostup = await db.get_user_dostup(message.from_user.id)
    if dostup is None or dostup < 2: return await message.reply("😢 У вас нет 2 уровня доступа!")

    info = command.args
    if info is None: return await message.reply(f"💻 Для очистки домашки используйте следующий синтакисис:\n<b>/dz_clear предмет</b>\n\nПример:\n<b>/dz_clear en1</b>\n\nДоступные предметы:\n<b>{get_text_list_lessons_with_code()}</b>")
    if info not in lessons: return await message.reply(f"❗️ Вы указали неверный код предмета!\n\nДоступные предметы:\n<b>{get_text_list_lessons_with_code()}</b>")

    await db.clear_dz(message.from_user.id, info)
    await message.reply(f"☑️ Вы очистили домашку по <b>{lessons[info][1]}</b>")
    return await bot.send_message(logs_group, f"🤨 Пользователь: {hlink(message.from_user.first_name, message.from_user.url)}\nДействие: <b>обнуление домашки по {lessons[info][1]}</b>\nРезультат: <b>успешно</b>")


@dp.message(Command('dz_setadmin'))
async def clear_cmd(message: types.Message, command: CommandObject):
    dostup = await db.get_user_dostup(message.from_user.id)
    if dostup is None or dostup < 3: return await message.reply("😢 У вас нет 3 уровня доступа!")

    if command.args is None: return await message.reply("❗️ Неверный синтаксис!\n\nИспользуйте: <b>/dz_setadmin id lvl</b>\nПример: <b>/dz_setadmin 1231231234 2</b>")
    info = command.args.split(maxsplit=1)
    if len(info) < 2: return await message.reply("❗️ Неверный синтаксис!\n\nИспользуйте: <b>/dz_setadmin id lvl</b>\nПример: <b>/dz_setadmin 1231231234 2</b>")

    if await db.get_user_dostup(message.from_user.id) is None: return await message.reply("❗️ Пользователь не зарегистрирован в системе бота!")

    try: 
        if int(info[1]) < 0 and int(info[1]) > 3: return await message.reply("❗️ Уровень должен быть больше или равен 0, но меньше или равен 3!")
    except ValueError:
        return await message.reply("❗️ В аргументах команды нельзя использовать буквы!")
        
    await db.set_user_dostup(message.from_user.id, int(info[1]))
    await message.reply(f"😁 Вы успешно назначили пользователю с ID <b>{info[0]}</b> доступ уровня <b>{info[1]}</b>!")
    return await bot.send_message(int(info[0]), f"😁 Вам успешно выдали доступ уровня <b>{info[1]}</b>!")


# Главный поток
async def main():
    await db.check_db()
    dp.include_router(router)
    print(f"{datetime.now()} | ДомашкоБот v. 3.0 успешно запущен!")
    return await dp.start_polling(bot)


if __name__ == '__main__':
    run(main())
