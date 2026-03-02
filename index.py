import discord
from discord.ext import commands
from discord import app_commands
from google import genai
from dotenv import load_dotenv
import json
import os
from google.genai import errors
import asyncio
load_dotenv()
from flask import Flask
from threading import Thread
can_send = True

# এটি পাইথনের 'express' এর মতো কাজ করবে
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# এখন তোমার বটের মেইন অংশে এটি কল করো
keep_alive()
gemini_busy = False
api = os.getenv("API")
token = os.getenv("TOKEN")
clientg = genai.Client(api_key=api)
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=None, intents=intents)

async def load_json():
    try:
        with open("channels.json", "r") as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
async def save_json(data):
    with open("channels.json", "w") as f:
        json.dump(data, f, indent=4)
@client.event
async def on_ready():
    try:
        synched = await client.tree.sync()
        if (len(synched) == 0):
            return print("No command found")
        print(f"Successfully loaded {len(synched)} commands")
    except Exception as e:
        print(f"Something went wrong! Error: {e}")
chat = clientg.chats.create(model="gemini-3-flash-preview")
@client.event
async def on_message(message):
    global gemini_busy
    global can_send
    if message.author == client.user:
        return
    if (not can_send):
        return await message.reply("Slow down!")
    data = await load_json()
    guild_id = str(message.guild.id)
    channelid = str(message.channel.id)
    if guild_id in data:
        if channelid == data[guild_id]:
            try:
                if gemini_busy : 
                    return await message.reply("Wait 5minutes! Gemini is busy!")
                
                msg = await message.reply("Generating contents...")
                response = chat.send_message(f"Hello, I'm {message.author.name}. Answer the prompt in less than 1800 character: promt: {message.content}")
                await msg.edit(content=response.text)
                can_send = False
                await asyncio.sleep(60)
                can_send = True
            except Exception as e:
                if ("429" in str(e)):
                    gemini_busy = True
                    await message.reply("Wait 5minutes! Gemini is busy!")
                    await asyncio.sleep(600)
                    gemini_busy = False
                else:
                    print(f"Error: {e}")

            
@client.tree.command(name="setchannel", description="set channel where gemini will reply")
@app_commands.describe(channel="pls select a channel")
async def setchannel(interaction: discord.Interaction, channel : discord.TextChannel):
    data = await load_json()
    guild_id = str(interaction.guild.id)
    channelid = str(channel.id)
    try:
        await interaction.response.defer()
        data[guild_id] = channelid
        await interaction.followup.send("Successfully set this channel for gemini's reply")
    except Exception as e:
        print(f"Something went wrong! Error: {e}")
    await save_json(data)
client.run(token)
