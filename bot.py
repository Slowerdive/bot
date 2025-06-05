import sqlite3
import random
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7193491431:AAGqAvjzC0GScQOYVwtIP1frDgacPMoALSc"

def init_db():
    conn = sqlite3.connect('articles.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_articles (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            user_id INTEGER
        )
    ''')
    conn.commit()
    return conn

db_connection = init_db()

async def is_valid_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Привет! Я бот, который поможет не забыть прочитать статьи, найденные тобой в интернете\n\n"
        "- Чтобы я запомнил статью, достаточно передать мне ссылку на нее. К примеру, https://example.com.\n"
        "- Чтобы получить случайную статью, достаточно передать мне команду /get_article.\n\n"
        "Но помни: отдавая статью тебе на прочтение, она больше не хранится в моей базе. Так что тебе точно нужно ее изучить."
    )
    await update.message.reply_text(welcome_text)

async def get_article(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = db_connection.cursor()
    cursor.execute('SELECT url FROM saved_articles WHERE user_id = ?', (update.message.from_user.id,))
    articles = cursor.fetchall()

    if not articles:
        await update.message.reply_text("Вы пока не сохранили ни одной статьи. Если нашли что-то стоящее, я жду!")
    else:
        article = random.choice(articles)[0]
        cursor.execute('DELETE FROM saved_articles WHERE url = ? AND user_id = ?', (article, update.message.from_user.id))
        db_connection.commit()
        response = (
            "Вы готовы прочитать:\n"
            f"{article}\n"
            "Самое время это сделать!"
        )
        await update.message.reply_text(response, disable_web_page_preview=True)

async def save_article(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.message.from_user.id

    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("Пожалуйста, отправьте ссылку, начинающуюся с http:// или https://")
        return

    cursor = db_connection.cursor()
    cursor.execute('SELECT 1 FROM saved_articles WHERE url = ? AND user_id = ?', (url, user_id))
    if cursor.fetchone():
        await update.message.reply_text("Упс, вы уже это сохранили")
        return

    if not await is_valid_url(url):
        await update.message.reply_text("Не удалось проверить ссылку. Возможно, она не работает.")
        return

    cursor.execute('INSERT INTO saved_articles (url, user_id) VALUES (?, ?)', (url, user_id))
    db_connection.commit()
    await update.message.reply_text("Сохранил, спасибо!")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_article", get_article))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_article))

    app.run_polling()

if __name__ == "__main__":
    main()