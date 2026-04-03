# replace_link_bot.py
import re
import logging
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import EditMessageRequest

# ======= ТВОИ ДАННЫЕ =======
api_id = 33836905
api_hash = "7bb34a03db8ecbf1d530c700b783fc40"
session_name = "replace_links"
DEFAULT_LIMIT = 300
CHANNEL = "@kani423123"
# ===========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("replace_links.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

client = TelegramClient(session_name, api_id, api_hash)
url_re = re.compile(r"https?://\S+")


@client.on(events.NewMessage(pattern=r"^/replace\s+(https?://\S+)(?:\s+(\d+))?$"))
async def replace_handler(event):
    if not event.is_private:
        await event.respond("Отправь команду в личку этому аккаунту.")
        return

    new_link = event.pattern_match.group(1)
    limit = int(event.pattern_match.group(2)) if event.pattern_match.group(2) else DEFAULT_LIMIT

    logging.info(f"Команда replace: new_link={new_link}, limit={limit}")
    await event.respond(f"🔁 Начинаю замену ссылок на {new_link}...")

    updated = 0

    async for msg in client.iter_messages(CHANNEL, limit=limit):

        text = msg.message or ""
        if not text:
            continue

        m = url_re.search(text)
        if not m:
            continue

        old_link = m.group(0)
        new_text = text.replace(old_link, new_link)

        # === пересобираем кнопки если есть ===
        reply_markup = None
        if msg.buttons:
            rows = []
            for row in msg.buttons:
                new_row = []
                for btn in row:
                    t = btn.text
                    u = getattr(btn, "url", None)
                    if u and url_re.search(u):
                        new_row.append(Button.url(t, new_link))
                    elif u:
                        new_row.append(Button.url(t, u))
                    else:
                        new_row.append(Button.text(t))
                rows.append(new_row)
            reply_markup = rows

        try:
            await client(EditMessageRequest(
                peer=msg.peer_id,
                id=msg.id,
                message=new_text,
                entities=msg.entities,        # ← сохраняем форматирование
                reply_markup=reply_markup     # ← кнопки
            ))

            updated += 1
            logging.info(f"Updated message {msg.id}")

        except Exception as e:
            logging.exception(f"Ошибка редактирования {msg.id}: {e}")

    await event.respond(f"✅ Готово! Обновлено {updated} сообщений.")
    logging.info(f"Completed: {updated} updates.")


if __name__ == "__main__":
    client.start()
    me = client.loop.run_until_complete(client.get_me())
    print(f"Logged in as @{me.username}")
    client.run_until_disconnected()
