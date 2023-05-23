import sqlalchemy
from discord.ext import commands
import discord
import random
import asyncio
import datetime
from discord.ui import Button, View
import os
import pandas as pd
import matplotlib.pyplot as plt
import dataframe_image as dfi
import numpy as np

class GameConfig(commands.Cog):
    def __init__(self, client, name='GameConfig Cog'):
        self.engine = sqlalchemy.create_engine( "mysql+pymysql://" + os.getenv('SQL_USERNAME') + ":" + os.getenv('SQL_PASSWORD') + "@127.0.0.1/xbot")

    @commands.command()
    async def add_players(self, ctx, *args):
        with self.engine.connect() as conn:
            players = []

            for player in args:
                players.append(await ctx.guild.fetch_member(int(player[2:-1])))
            
            for player in players:
                conn.execute("INSERT INTO xbot.players (player_id, player_name) VALUES ('" + str(player.id) + "', '" + player.name + "')")
            await ctx.send("Players added.")

    @commands.command()
    async def set_tribes(self, ctx, *args):
        with self.engine.connect() as conn:
            roles = []

            try:
                for tribe in args:
                    await roles.append(ctx.guild.get_role(int(tribe[3:-1])))
            except:
                return
                
            for role in roles:
                conn.execute("INSERT INTO xbot.tribes (tribe_id, tribe_name) VALUES ('" + str(role.id) + "', '" + str(role.name) + "')")
    
    @commands.command()
    async def create_alliance_category(self, ctx):
        with self.engine.connect() as conn:
            category = await ctx.guild.create_category("Alliances")
            if category:
                conn.execute("INSERT INTO xbot.categories (category_id, category_name) VALUES ('" + str(category.id) + "', '" + str(category.name) + "')")







        


async def setup(bot):
    await bot.add_cog(GameConfig(bot))