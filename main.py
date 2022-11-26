import os
import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
from setuptools import setup, find_packages
import logging

from cogs.xquester import Xquester

intents = discord.Intents().all()

logging.basicConfig(level=logging.INFO)

client = commands.Bot(command_prefix = '-', intents=intents)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

@client.event
async def on_ready():
	print('Hello XTRON, I am fully operational')

@client.command()
async def load(ctx, extension):
	await client.load_extension(f'cogs.{extension}')
	print(f'Loaded {extension}.py')

@client.command()
async def unload(ctx, extension):
	await client.unload_extension(f'cogs.{extension}')
	print(f'Unloaded {extension}.py')

@client.command()
async def reload(ctx, extension):
	await client.unload_extension(f'cogs.{extension}')
	await client.load_extension(f'cogs.{extension}')
	print(f'Reloaded {extension}.py')

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")
            print("Loaded")

async def main():
    async with client:
        await load_extensions()
        await client.start(TOKEN)

asyncio.run(main())