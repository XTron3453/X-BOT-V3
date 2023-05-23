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

class Alliances(commands.Cog):
    def __init__(self, client, name='Specgames Cog'):
        self.engine = sqlalchemy.create_engine( "mysql+pymysql://" + os.getenv('SQL_USERNAME') + ":" + os.getenv('SQL_PASSWORD') + "@127.0.0.1/xbot")

    @commands.command()
    async def create_alliance(self, ctx, *args):
        with self.engine.connect() as conn:

            alliance_members = []

            try:
                for player_name in args:
                    alliance_members.append(conn.execute("SELECT player_id FROM xbot.players WHERE player_name = '" + player_name + "'").first()[0])
            except:
                await ctx.send(ctx.author.mention + ", one of these players is not found. Please check your list again for proper spelling.")
                return

            if len(alliance_members) > 1:
                alliance_id_query = '('
                player_id_query = "('" + str(ctx.author.id) + "', "

                for index, player_id in enumerate(alliance_members):
                    order_id_query = order_id_query + 'player_' + str(index + 1) + '_id, '
                    player_id_query = player_id_query + "'" + str(player_id) + "', "

                order_id_query = order_id_query[:-2] + ')'
                player_id_query = player_id_query[:-2] + ')'

                try:
                    if len(set(alliance_members)) == len(alliance_members):
                        conn.execute('INSERT INTO xbot.alliances ' + order_id_query + ' VALUES ' + player_id_query)
                    else:
                        await ctx.send(ctx.author.mention + ", your alliance has a repeating player!")
                except:
                    await ctx.send(ctx.author.mention + ", this bootlist already exists! Change some of your placements please.")
            else:
                await ctx.send(ctx.author.mention + ", there are not enough players in this alliance.")
        

    async def name_alliance(self, ctx, alliance_id=None):
        pass
        #If None, rename the current alliance
        #If an ID is passed, rename that alliance

    async def archive_alliance(self, ctx, alliance):
        pass
        #If None, archive the current alliance
        #If an ID is passed, archive that alliance



async def setup(bot):
    await bot.add_cog(Alliances(bot))