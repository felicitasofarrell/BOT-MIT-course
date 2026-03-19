from dotenv import load_dotenv
load_dotenv()

import os
import discord
from openai import OpenAI

# Environment variables
TOKEN = os.getenv("TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

if not TOKEN:
    raise ValueError("Missing TOKEN environment variable.")

if not OPENAI_KEY:
    raise ValueError("Missing OPENAI_KEY environment variable.")

# OpenAI client
oa_client = OpenAI(api_key=OPENAI_KEY)

# Discord client configuration
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def split_message(text: str, max_length: int = 1900) -> list[str]:
    """
    Split a long message into smaller chunks so it fits Discord limits.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""

    for line in text.splitlines(keepends=True):
        if len(current) + len(line) <= max_length:
            current += line
        else:
            if current:
                chunks.append(current)
            current = line

    if current:
        chunks.append(current)

    return chunks


def call_openai(question: str) -> str:
    """
    Send the user's question to OpenAI and return the assistant's response.
    """
    completion = oa_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful onboarding assistant. "
                    "Answer clearly, warmly, and practically. "
                    "Keep answers concise but useful. "
                    "If the question is unclear, ask for clarification."
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    response = completion.choices[0].message.content
    return response.strip() if response else "Sorry, I could not generate a response."


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    # Ignore the bot's own messages
    if message.author == client.user:
        return

    content = message.content.strip()

    # Simple hello command
    if content.startswith("$hello"):
        await message.channel.send("Hello!")
        return

    # Question command
    if content.startswith("$question"):
        question = content[len("$question"):].strip()

        if not question:
            await message.channel.send(
                "Please include a question after `$question`.\n"
                "Example: `$question How do I request time off?`"
            )
            return

        try:
            await message.channel.send("Thinking...")

            print(f"User message: {content}")
            print(f"Extracted question: {question}")

            response = call_openai(question)

            print(f"Assistant response: {response}")
            print("---")

            for chunk in split_message(response):
                await message.channel.send(chunk)

        except Exception as e:
            print(f"Error while handling question: {e}")
            await message.channel.send(
                "Sorry, something went wrong while generating the response."
            )


client.run(TOKEN)
