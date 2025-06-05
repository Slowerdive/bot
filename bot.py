import sqlite3
import random
import aiohttp
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Инициализация бота с настройками по умолчанию
API_TOKEN = '7193491431:AAGqAvjzC0GScQOYVwtIP1frDgacPMoALSc'

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Инициализация базы данных
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        user_id INTEGER
    )
''')
conn.commit()


async def check_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    except:
        return False


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Я бот, который поможет не забыть прочитать статьи, найденные тобою в интернете\n\n"
        "Чтобы я запомнил статью, достаточно передать мне ссылку на неё. К примеру https://example.com.\n"
        "Чтобы получить случайную статью, достаточно передать мне команду /get_article.\n\n"
        "Но помни: отдавая статью тебе на прочтение, она больше не хранится в моей базе. Так что тебе точно нужно её изучить."
    )


@dp.message(Command("get_article"))
async def get_article(message: Message):
    cursor.execute('SELECT url FROM articles WHERE user_id = ?', (message.from_user.id,))
    articles = cursor.fetchall()

    if not articles:
        await message.answer("Вы пока не сохранили ни одной статьи. Если найдёшь что-то стоящее, я жду!")
    else:
        article = random.choice(articles)
        cursor.execute('DELETE FROM articles WHERE url = ? AND user_id = ?', (article[0], message.from_user.id))
        conn.commit()
        await message.answer(
            f"Все готовы прочитать:\n{article[0]}\nСамое время это сделать!",
            disable_web_page_preview=True
        )


@dp.message()
async def save_article(message: Message):
    url = message.text.strip()

    if not (url.startswith('http://') or url.startswith('https://')):
        await message.answer("Пожалуйста, отправь корректную ссылку, начинающуюся с http:// или https://")
        return

    cursor.execute('SELECT url FROM articles WHERE url = ? AND user_id = ?', (url, message.from_user.id))
    if cursor.fetchone():
        await message.answer("Упс, вы уже это сохранили :)")
        return

    is_valid = await check_url(url)
    if not is_valid:
        await message.answer("По этой ссылке ничего не найдено")
        return

    cursor.execute('INSERT INTO articles (url, user_id) VALUES (?, ?)', (url, message.from_user.id))
    conn.commit()
    await message.answer("Статья успешно добавлена в базу!")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())