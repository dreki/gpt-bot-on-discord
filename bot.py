import json
import os
import sqlite3

import discord
from openai import OpenAI

# Get Discord bot key from env var "DISCORD_BOT_KEY"
DISCORD_BOT_KEY = os.getenv("DISCORD_BOT_KEY")

# Get OpenAI key from env var "OPEN_AI_KEY"
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")

GPT_CONTEXT_MESSAGE = {
    "role": "system",
    "content": "Mephisto Chat, inspired by the cunning Mephistopheles from Goethe's \"Faust,\" engages in dialogue with a blend of 19th-century cultural references and Faustian themes. It is adept in offering wise, witty, and sometimes sardonic insights, drawing from its rich background of literature and philosophy. Mephisto Chat maintains a balance of formality and playful charm, mirroring the enigmatic and slightly aloof nature of its character. It handles conversations with a poetic humor, adding a sophisticated twist to interactions. This GPT is programmed to avoid any form of racism, ableism, or bias, ensuring respectful and thought-provoking exchanges. It addresses users in a formal yet inviting manner, encouraging an engaging dialogue. Whether it's discussing literature, philosophy, or everyday dilemmas, Mephisto Chat guides users through a journey of intellectual exploration, always hinting at deeper meanings and the complexity of human nature, much like its namesake in \"Faust.\""
}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

openai_client = OpenAI(api_key=OPEN_AI_KEY)

# Create a connection to the SQLite database
db = sqlite3.connect('conversation_history.db')
db_cursor = db.cursor()


def create_conversation_history_table():
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_history (
            user_id TEXT PRIMARY KEY,
            history TEXT
        )
    ''')
    db.commit()


create_conversation_history_table()


def save_conversation_history(user_id, history):
    # Convert the history to a JSON string
    history_json = json.dumps(history)

    # Insert or update the history in the database
    db_cursor.execute('''
        INSERT INTO conversation_history (user_id, history)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET history = excluded.history
    ''', (user_id, history_json))

    # Commit the changes
    db.commit()


def load_conversation_history(user_id) -> list:
    # Retrieve the history from the database
    db_cursor.execute('SELECT history FROM conversation_history WHERE user_id = ?', (user_id,))

    # Fetch the result
    result = db_cursor.fetchone()

    # If a result was found, convert it from a JSON string to a dictionary and return it
    if result is not None:
        return json.loads(result[0])
    else:
        return [GPT_CONTEXT_MESSAGE]


# conversation_history = load_conversation_history()


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_guild_join(guild):
    try:
        # Change the bot's nickname upon joining a guild
        await guild.me.edit(nick="Mephisto")
        print(f"Changed nickname in {guild.name}")
    except Exception as e:
        print(f"Failed to change nickname in {guild.name}: {e}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.id in [m.id for m in message.mentions]:  # Check if the bot is mentioned
        user_input = message.content.replace(f'<@{client.user.id}>', '').strip()

        conversation_history = load_conversation_history(message.author.id)

        # Add the user's message to the conversation history
        conversation_history.append({"role": "user", "content": user_input})

        response = openai_client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=conversation_history
        )

        # Add the bot's response to the conversation history
        bot_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": bot_response})

        # Save the conversation history
        save_conversation_history(
            user_id=message.author.id,
            history=conversation_history
        )

        # Split the bot's response into chunks and send each as a separate message
        chunks = [bot_response[i:i + 1900] for i in range(0, len(bot_response), 1900)]
        for chunk in chunks:
            await message.reply(chunk)


client.run(DISCORD_BOT_KEY)
