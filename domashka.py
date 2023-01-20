import sqlite3
import datetime
import aiogram
import logging
import configparser

from aiogram import Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage

datetime.datetime.now().min

db = sqlite3.connect('domashka.db', check_same_thread=False)
c = db.cursor()


config = configparser.ConfigParser()
config.read("settings.ini")

#Настройки бота

logs_group = int(config["Main"]["logs_group"]) #Группа для логов
bot = aiogram.Bot(str(config["Main"]["token"]), parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

#///////////////////////////////////////////////////

dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)

date = datetime.datetime.now()
print(str(date), "|" + " ДомашкоБот v. 1.0 успешно запущен!")

# ключ: предмет в дательном падеже
predmets = {'alg': 'алгебре', 'en1': 'первой группе английского', 'en2': 'второй группе английского', 'bio': 'биологии', 'geom': 'геометрии', 'geog': 'географии',
            'chem': 'химии', 'info1': 'первой группе информатики', 'info2': 'второй группе информатики', 'litra': 'литературе', 'nem1': 'первой группе немецкого',
            'nem2': 'второй группе немецкого', 'obchest': 'обществознание', 'history': 'истории', 'russian': 'русскому языку', 'techn1': 'технологии(мальчики)',
            'techn2': 'технологии(девочки)', 'phisic': 'физике'}


@dp.message_handler(commands=['start'])
async def start(message):
    user_id = message.from_user.id
    c.execute(f"SELECT id FROM users WHERE id = {user_id}")
    data = c.fetchone()[0]

    if data is None:
        dostup = 0
        name = "Не установлено"
        surname = "Не установлено"

        user_info = (int(user_id), str(name), str(surname), int(dostup))
        c.execute("INSERT INTO users(id, name, surname, dostup) VALUES(?, ?, ?, ?)",(user_info))
        db.commit()
        await message.reply("🎉 Вы успешно зарегистрировались в боте! Ваш ID телеграм - *" + str(user_id) + '*', parse_mode= "Markdown")

    else:
        await message.reply("🔑 Успешный вход!")


@dp.message_handler(commands=['dz'])
async def check_dz(message):
    user_id = message.from_user.id
    c.execute(f"SELECT dostup FROM users WHERE id = {user_id}")
    data = c.fetchone()

    if int(data[0]) < 1 or data[0] is None:
        await message.reply("😢 У вас меньше 1 уровня доступа!")

    else:
        kb = types.InlineKeyboardMarkup()
        kb_algebra = types.InlineKeyboardButton(text='Алгебра', callback_data='check_algebra')
        kb_english = types.InlineKeyboardButton(text='Английский язык', callback_data='check_english')
        kb_biology = types.InlineKeyboardButton(text='Биология', callback_data='check_biology')
        kb_geogr = types.InlineKeyboardButton(text='География', callback_data='check_geogr')
        kb_geoma = types.InlineKeyboardButton(text='Геометрия', callback_data='check_geoma')
        kb_chimiya = types.InlineKeyboardButton(text='Химия', callback_data='check_chimiya')
        kb_informat = types.InlineKeyboardButton(text='Информатика', callback_data='check_informat')
        kb_litra = types.InlineKeyboardButton(text='Литература', callback_data='check_litra')
        kb_nemec = types.InlineKeyboardButton(text='Немецкий язык', callback_data='check_nemec')
        kb_obshestvo = types.InlineKeyboardButton(text='Обществознание', callback_data='check_obshestvo')
        kb_history = types.InlineKeyboardButton(text='История', callback_data='check_history')
        kb_russian = types.InlineKeyboardButton(text='Русский язык', callback_data='check_russian')
        kb_techno = types.InlineKeyboardButton(text='Технология', callback_data='check_techno')
        kb_phisic = types.InlineKeyboardButton(text='Физика', callback_data='check_phisic')

        kb.add(kb_algebra, kb_english, kb_biology, kb_geogr, kb_geoma, kb_chimiya, kb_informat, kb_litra, kb_nemec, kb_obshestvo, kb_history, kb_russian, kb_techno, kb_phisic)
        return await message.reply('🛍 Выберите *школьный предмет* из списка ниже', parse_mode= "Markdown", reply_markup=kb)



async def check_dz(call: types.CallbackQuery, name, db_name): # объект CallbackQuery, имя в дательном падеже, запись в БД
    c.execute(f"SELECT dz, author, time FROM domashka WHERE predmet = '{db_name}'")
    data = c.fetchone()

    if data[0] is not None:
        return await bot.answer_callback_query(call.id, f'\t\t📔 Доска д/з по {name}\n\n😇 Автор: @{data[1]}\n🕓 Время добавления: {data[2]}\n\n📚 Задание:\n{data[0]}', show_alert=True)
            
    else:
        return await bot.answer_callback_query(call.id, f"📔 Домашка по {name} отсутствует!", show_alert=True)
        

@dp.callback_query_handler()
async def callback_check_dz(call: types.CallbackQuery):
    if call.from_user.id != call.message.reply_to_message.from_user.id:
        return await bot.answer_callback_query(call.id, f"Вы не можете использовать чужие сообщения!") 

    if call.data.startswith('check'):
        if call.data == 'check_algebra':
            return await check_dz(call, 'алгебре', 'alg')

        elif call.data == 'check_enboys':
            return await check_dz(call, 'английскому языку(Иванова)', 'en1')
            
        elif call.data == 'check_engirls':
            return await check_dz(call, 'английскому языку(Хуснуллина)', 'en2')
        
        elif call.data == 'check_biology':
            return await check_dz(call, 'биологии', 'bio')

        elif call.data == 'check_geogr':
            return await check_dz(call, 'географии', 'geog')
        
        elif call.data == 'check_geoma':
            return await check_dz(call, 'геометрии', 'geom')
        
        elif call.data == 'check_chimiya':
            return await check_dz(call, 'химии', 'chem')

        elif call.data == 'check_iboys':
            return await check_dz(call, 'информатике(Санников)', 'info1')
            
        elif call.data == 'check_igirls':
            return await check_dz(call, 'информатике(Андреева)', 'info2')
        
        elif call.data == 'check_litra':
            return await check_dz(call, 'литературе', 'litra')

        elif call.data == 'check_nboys':
            return await check_dz(call, 'немецкому языку(Ильина)', 'nem1')
            
        elif call.data == 'check_ngirls':
            return await check_dz(call, 'немецкому языку(Разина)', 'nem2')

        elif call.data == 'check_obshestvo':
            return await check_dz(call, 'обществознанию', 'obchest')
        
        elif call.data == 'check_history':
            return await check_dz(call, 'истории', 'history')
        
        elif call.data == 'check_russian':
            return await check_dz(call, 'русскому языку', 'russian')

        elif call.data == 'check_tboys':
            return await check_dz(call, 'технологии(Мальчики)', 'techn1')
            
        elif call.data == 'check_tgirls':
            return await check_dz(call, 'технологии(Девочки)', 'techn2')

        elif call.data == 'check_phisic':
            return await check_dz(call, 'физике', 'phisic')

        
        elif call.data == 'check_techno':
            kb = types.InlineKeyboardMarkup()
            kb_tboys = types.InlineKeyboardButton(text='Мальчики', callback_data='check_tboys')
            kb_tgirls = types.InlineKeyboardButton(text='Девочки', callback_data='check_tgirls')
            kb_return = types.InlineKeyboardButton(text='Назад', callback_data='return')
            kb.add(kb_tboys, kb_tgirls, kb_return)
            return await call.message.edit_reply_markup(reply_markup=kb)

        elif call.data == 'check_nemec':
            kb = types.InlineKeyboardMarkup()
            kb_nboys = types.InlineKeyboardButton(text='Молодая (Ильина)', callback_data='check_nboys')
            kb_ngirls = types.InlineKeyboardButton(text='Старая (Разина)', callback_data='check_ngirls')
            kb_return = types.InlineKeyboardButton(text='Назад', callback_data='return')
            kb.add(kb_nboys, kb_ngirls, kb_return)
            return await call.message.edit_reply_markup(reply_markup=kb)

        elif call.data == 'check_informat':
            kb = types.InlineKeyboardMarkup()
            kb_iboys = types.InlineKeyboardButton(text='Санников', callback_data='check_iboys')
            kb_igirls = types.InlineKeyboardButton(text='Андреева', callback_data='check_igirls')
            kb_return = types.InlineKeyboardButton(text='Назад', callback_data='return')
            kb.add(kb_iboys, kb_igirls, kb_return)
            return await call.message.edit_reply_markup(reply_markup=kb)

        elif call.data == 'check_english':
            kb = types.InlineKeyboardMarkup()
            kb_enboys = types.InlineKeyboardButton(text='Иванова', callback_data='check_enboys')
            kb_engirls = types.InlineKeyboardButton(text='Хуснуллина', callback_data='check_engirls')
            kb_return = types.InlineKeyboardButton(text='Назад', callback_data='return')
            kb.add(kb_enboys, kb_engirls, kb_return)
            return await call.message.edit_reply_markup(reply_markup=kb)

    
    elif call.data == 'return':
        kb = types.InlineKeyboardMarkup()
        kb_algebra = types.InlineKeyboardButton(text='Алгебра', callback_data='check_algebra')
        kb_english = types.InlineKeyboardButton(text='Английский язык', callback_data='check_english')
        kb_biology = types.InlineKeyboardButton(text='Биология', callback_data='check_biology')
        kb_geogr = types.InlineKeyboardButton(text='География', callback_data='check_geogr')
        kb_geoma = types.InlineKeyboardButton(text='Геометрия', callback_data='check_geoma')
        kb_chimiya = types.InlineKeyboardButton(text='Химия', callback_data='check_chimiya')
        kb_informat = types.InlineKeyboardButton(text='Информатика', callback_data='check_informat')
        kb_litra = types.InlineKeyboardButton(text='Литература', callback_data='check_litra')
        kb_nemec = types.InlineKeyboardButton(text='Немецкий язык', callback_data='check_nemec')
        kb_obshestvo = types.InlineKeyboardButton(text='Обществознание', callback_data='check_obshestvo')
        kb_history = types.InlineKeyboardButton(text='История', callback_data='check_history')
        kb_russian = types.InlineKeyboardButton(text='Русский язык', callback_data='check_russian')
        kb_techno = types.InlineKeyboardButton(text='Технология', callback_data='check_techno')
        kb_phisic = types.InlineKeyboardButton(text='Физика', callback_data='check_phisic')

        kb.add(kb_algebra, kb_english, kb_biology, kb_geogr, kb_geoma, kb_chimiya, kb_informat, kb_litra, kb_nemec, kb_obshestvo, kb_history, kb_russian, kb_techno, kb_phisic)
        return await call.message.edit_reply_markup(reply_markup=kb)


@dp.message_handler(commands=['dz_new'])
async def new_dz(message: types.Message):
    if message.chat.type != 'private':
        return await message.reply("❌ Это можно использовать только в личке бота!")

    user_id = message.from_user.id
    c.execute(f"SELECT dostup FROM users WHERE id = {user_id}")
    data = c.fetchone()

    if int(data[0]) < 2 or data[0] is None:
        return await message.reply("У вас меньше 2 уровня доступа!")

    info = message.get_args().split(' ', maxsplit=1)

    if len(info) <= 1:
        return await message.reply("<b>💻 Для добавления домашки используйте следующий синтакисис:\n/dz_new *предмет* *домашка*\n\nПример:\n/dz_new en1 1. Учебник страница 51 упражнение устно, рабочая тетрадь стр 31 полностью\n\nДоступные предметы:\n\
            - alg - алгбера\n\
            - en1 - первая группа английского\n\
            - en2 - вторая группа английского\n\
            - bio - биология\n\
            - geom - геометрия\n\
            - geog - геометрия\n\
            - chem - химия\n\
            - info1 - первая группа информатики\n\
            - info2 - вторая группа информатики\n\
            - litra - литература\n\
            - nem1 - первая группа немецкого\n\
            - nem2 - вторая группа немецкого\n\
            - obchest - обществознание\n\
            - history - история\n\
            - russian - русский язык\n\
            - techn1 - первая группа технологии\n\
            - techn2 - вторая группа технологии\n\
            - phisic - физика</b>")

    if info[0] not in predmets:
        return await message.reply("<b>❗️ Вы указали неверный код предмета!\n\nДоступные предметы:\n\
            - alg - алгбера\n\
            - en1 - первая группа английского\n\
            - en2 - вторая группа английского\n\
            - bio - биология\n\
            - geom - геометрия\n\
            - geog - геометрия\n\
            - chem - химия\n\
            - info1 - первая группа информатики\n\
            - info2 - вторая группа информатики\n\
            - litra - литература\n\
            - nem1 - первая группа немецкого\n\
            - nem2 - вторая группа немецкого\n\
            - obchest - обществознание\n\
            - history - история\n\
            - russian - русский язык\n\
            - techn1 - первая группа технологии\n\
            - techn2 - вторая группа технологии\n\
            - phisic - физика</b>")


    c.execute(f"INSERT INTO logs(user_id, action, result) VALUES({user_id}, 'изменение д/з по {info[0]}', '{info[1]}')")
    db.commit()
    c.execute(f"UPDATE domashka SET dz = '{info[1]}', author = '{message.from_user.username}', time = '{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}' WHERE predmet = '{info[0]}'")
    db.commit()
    await bot.send_message(logs_group, f"🤨 Замечена активность!\n\nID пользователя: <b>{user_id}</b>\nДействие: <b>изменение д/з по {info[0]}</b>\nРезультат: <b>{info[1]}</b>")
    return await message.reply(f"☑️ Вы успешно изменили домашку по <b>{predmets[info[0]]}</b> на:\n\n<b>{info[1]}</b>")

@dp.message_handler(commands=['dz_help'])
async def help_cmd(message: types.Message):
    user_id = message.from_user.id
    c.execute(f"SELECT dostup FROM users WHERE id = {user_id}")
    data = c.fetchone()

    if int(data[0]) < 1 or data[0] is None:
        return await message.reply("У вас меньше 1 уровня доступа!")

    return await message.reply("😍Команды ДомашкоБота:\n\n<b>/dz</b> - узнать домашнее задание(1+ уровень доступа)\n<b>/dz_help</b> - открыть меню помощи(1+ уровень доступа)\n<b>/dz_new *код предмета* *домашнее задание*</b> - обновить домашнее задание(2+ уровень доступа)\n<b>/dz_clear *код предмета*</b> - очистить домашнее задание(2+ уровень доступа)")


@dp.message_handler(commands=['dz_clear'])
async def clear_cmd(message: types.Message):
    user_id = message.from_user.id
    c.execute(f"SELECT dostup FROM users WHERE id = {user_id}")
    data = c.fetchone()

    if int(data[0]) < 2 or data[0] is None:
        return await message.reply("У вас меньше 2 уровня доступа!")

    info = message.get_args()

    if len(info) <= 2:
        return await message.reply("<b>💻 Для обнуления домашки используйте следующий синтакисис:\n/dz_clear *предмет*\n\nПример:\n/dz_clear en1\n\nДоступные предметы:\n\
            - alg - алгбера\n\
            - en1 - первая группа английского\n\
            - en2 - вторая группа английского\n\
            - bio - биология\n\
            - geom - геометрия\n\
            - geog - геометрия\n\
            - chem - химия\n\
            - info1 - первая группа информатики\n\
            - info2 - вторая группа информатики\n\
            - litra - литература\n\
            - nem1 - первая группа немецкого\n\
            - nem2 - вторая группа немецкого\n\
            - obchest - обществознание\n\
            - history - история\n\
            - russian - русский язык\n\
            - techn1 - первая группа технологии\n\
            - techn2 - вторая группа технологии\n\
            - phisic - физика</b>")

    if info not in predmets:
        return await message.reply("<b>❗️ Вы указали неверный код предмета!\n\nДоступные предметы:\n\
            - alg - алгбера\n\
            - en1 - первая группа английского\n\
            - en2 - вторая группа английского\n\
            - bio - биология\n\
            - geom - геометрия\n\
            - geog - геометрия\n\
            - chem - химия\n\
            - info1 - первая группа информатики\n\
            - info2 - вторая группа информатики\n\
            - litra - литература\n\
            - nem1 - первая группа немецкого\n\
            - nem2 - вторая группа немецкого\n\
            - obchest - обществознание\n\
            - history - история\n\
            - russian - русский язык\n\
            - techn1 - первая группа технологии\n\
            - techn2 - вторая группа технологии\n\
            - phisic - физика</b>")


    c.execute(f"UPDATE domashka SET dz = null, author = null, time = null WHERE predmet = '{info}'")
    db.commit()
    c.execute(f"INSERT INTO logs(user_id, action, result) VALUES({user_id}, 'обнуление {info}', 'успешно')")
    db.commit()
    await bot.send_message(logs_group, f"🤨 Замечена активность!\n\nID пользователя: <b>{user_id}</b>\nДействие: <b>обнуление {info}</b>\nРезультат: <b>успешно</b>")
    return await message.reply(f"☑️ Вы обнулили домашку по <b>{predmets[info]}</b>")


@dp.message_handler(commands=['dz_setadmin'])
async def clear_cmd(message: types.Message):
    user_id = message.from_user.id
    c.execute(f"SELECT dostup FROM users WHERE id = {user_id}")
    data = c.fetchone()

    if int(data[0]) < 3 or data[0] is None:
        return await message.reply("❗️ У вас меньше 3 уровня доступа!")

    info = message.get_args().split(maxsplit=1)

    if len(info) < 2:
        return await message.reply("❗️ Неверный синтаксис!\n\nИспользуйте: <b>/dz_setadmin id lvl</b>\nПример: <b>/dz_setadmin 1231231234 2</b>")

    c.execute(f"SELECT id FROM users WHERE id = {info[0]}")
    data = c.fetchone()

    if data is None:
        return await message.reply("❗️ Пользователь не зарегистрирован в системе бота!")

    try:
        if int(info[1]) > -1 and int(info[1]) <= 3:
            c.execute(f"UPDATE users SET dostup = {info[1]} WHERE id = '{info[0]}'")
            db.commit()
            return await message.reply(f"❗️ Вы успешно назначили пользователю с ID <b>{info[0]}</b> доступ уровня <b>{info[1]}</b>!")

        else:
            return await message.reply("❗️ Уровень должен быть больше или равен 0, но меньше или равен 3!")
    
    except ValueError:
        return await message.reply("❗️ В аргументах команды нельзя использовать буквы!")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)