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
    async def set_role(self, ctx, type, *args):
        with self.engine.connect() as conn:
            roles = []

            try:
                for tribe in args:
                    roles.append(ctx.guild.get_role(int(tribe[3:-1])))
            except:
                await ctx.send('Error: one of the arguments passed is not a role. Try again with the ping.')
                return
                
            for role in roles:
                conn.execute("INSERT INTO xbot.roles (role_id, role_name, role_type) VALUES ('" + str(role.id) + "', '" + str(role.name) + "', '" + str(type) + "')")
    
            if len(args) == 1:
                await ctx.send('Role set as: ' + type)
            else:
                await ctx.send('Roles set as: ' + type)

    @commands.command()
    async def create_category(self, ctx, name):
        with self.engine.connect() as conn:
            category = await ctx.guild.create_category(name)
            if category:
                conn.execute("INSERT INTO xbot.categories (category_id, category_name) VALUES ('" + str(category.id) + "', '" + name + "')")








        


async def setup(bot):
    await bot.add_cog(GameConfig(bot))