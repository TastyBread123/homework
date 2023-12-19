import aiosqlite
from datetime import datetime
from configs.lessons_config import lessons

class Database:
    def __init__(self, database_name: str):
        self.database_name = database_name


    async def check_db(self):
        """
        Проверяет таблицу на наличие строчки с предметом

        RETURN:
        :new_lessons - список текущих предметов
        """

        async with aiosqlite.connect(self.database_name, check_same_thread=False) as db:
            old_lessons = await db.execute('SELECT predmet FROM domashka')
            old_lessons = await old_lessons.fetchall()

            new_lessons = []
            for i in old_lessons:
                if i[0] not in lessons:
                    await db.execute('DELETE FROM domashka WHERE predmet = ?', (i[0],))
                    await db.commit()
                    continue
                new_lessons.append(i[0])

            for i in lessons:
                if i not in new_lessons:
                    await db.execute("INSERT INTO domashka(predmet) VALUES(?)", (i,))
                    await db.commit()
                    new_lessons.append(i)

            return new_lessons


    async def add_user(self, user_info: tuple):
        """
        Добавляет кортеж из данных пользователя (user_info) в базу данных

        RETURN:
        :user_info, в случае успеха (id, first_name, last_name)
        :False, в случае ошибки

        :param user_info - Кортеж из следующей информации: id пользователя, username, уровень админки, ник в боте, количество варнов, уровень VIP, общее кол-во exp, кол-во exp необходимые до нового уровня, кол-во exp собранных для нового лвл, уровень
        """

        try:
            async with aiosqlite.connect(self.database_name, check_same_thread=False) as db:
                data = await db.execute(f"SELECT id FROM users WHERE id = {user_info[0]}")

                if await data.fetchone() is None:
                    await db.execute("INSERT INTO users(id, name, surname, dostup) VALUES(?, ?, ?, ?)", (user_info[0], user_info[1], user_info[2], 0))
                    await db.commit()
                    return user_info
                return False
        
        except aiosqlite.OperationalError:
            return 'Error'
        

    async def get_user_dostup(self, user_id: int):
         """
         Получить уровень доступа пользователя

         RETURN:
         :dostup - уровень доступа пользователя
         :None - пользователь не найден

         :param user_id - id пользователя
         """

         async with aiosqlite.connect(self.database_name, check_same_thread=False) as db:
                data = await db.execute(f"SELECT dostup FROM users WHERE id = ?", (user_id,))
                if data is None: return None
                data = await data.fetchone()
                return int(data[0])
         

    async def set_user_dostup(self, user_id: int, dostup: int):
        """
        Именить уровень доступа пользователя

         RETURN:
         :dostup - новый уровень доступа пользователя

         :param user_id - id пользователя
         :param dostup - новый уровень доступа
         """
        
        async with aiosqlite.connect(self.database_name, check_same_thread=False) as db:
            await db.execute(f"UPDATE users SET dostup = ? WHERE id = ?", (dostup, user_id))
            await db.commit()
            return dostup
         

    async def add_new_dz(self, author_id: int, author_link: str, lesson_code: str, text: str):
        """
        Изменить домашнее задание по предмету

        RETURN:
        :True - в любом случае

        :param author_id - id автора изменения домашки
        :param author_link - url автора изменения домашки
        :param lesson_code - код предмета
        :param text - новая домашка
        """

        async with aiosqlite.connect(self.database_name, check_same_thread=False) as db:
            await db.execute(f"INSERT INTO logs(user_id, action, result) VALUES(?, ?, ?)", (author_id, f'изменение д/з {lesson_code}', text))
            await db.execute(f"UPDATE domashka SET dz = ?, author = ?, time = ? WHERE predmet = ?", (text, author_link, datetime.now().strftime('%d.%m.%Y %H:%M:%S'), lesson_code))
            await db.commit()
            return True


    async def clear_dz(self, author_id: int, lesson_code: str):
        """
        Очистить домашнее задание по предмету

        RETURN:
        :True - в любом случае

        :param author_id - id автора очистки
        :param lesson_code - код предмета
        """
        
        async with aiosqlite.connect(self.database_name, check_same_thread=False) as db:
            await db.execute(f"UPDATE domashka SET dz = null, author = null, time = null WHERE predmet = ?", (lesson_code,))
            await db.execute(f"INSERT INTO logs(user_id, action, result) VALUES(?, ?, ?)", (author_id, f'очистка {lesson_code}', 'успешно'))
            await db.commit()
            return True
