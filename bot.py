import os

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

conversation_history = {}


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

        # Check if the user's ID is in the conversation history
        if message.author.id not in conversation_history:
            conversation_history[message.author.id] = [GPT_CONTEXT_MESSAGE]

        # Add the user's message to the conversation history
        conversation_history[message.author.id].append({"role": "user", "content": user_input})

        response = openai_client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=conversation_history[message.author.id]
        )

        # Add the bot's response to the conversation history
        bot_response = response.choices[0].message.content
        conversation_history[message.author.id].append({"role": "assistant", "content": bot_response})

        await message.reply(bot_response)


client.run(DISCORD_BOT_KEY)
