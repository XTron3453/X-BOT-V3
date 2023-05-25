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
            alliance_category = None
            spectator_role = None

            try:
                alliance_category_query = conn.execute("SELECT category_id FROM xbot.categories WHERE category_name = 'Alliances'")
                alliance_category_id = alliance_category_query.fetchone()[0]
                alliance_category = next(item for item in ctx.guild.categories if item.id == int(alliance_category_id))
            except:
               await ctx.send(ctx.author.mention + ", no alliance category has been set up.")
               return

            try:
                spectator_id = conn.execute("SELECT role_id FROM xbot.roles WHERE role_type = 'Spectators'").first()[0]
                spectator_role = ctx.guild.get_role(int(spectator_id))
            except:
                await ctx.send(ctx.author.mention + ", no spectator role has been set up.")
                return
            
            try:
                for player_name in args:
                    alliance_members.append(conn.execute("SELECT player_id FROM xbot.players WHERE player_name = '" + player_name + "'").first()[0])
            except:
                await ctx.send(ctx.author.mention + ", one of these players is not found. Please check your list again for proper spelling.")
                return

            if len(alliance_members) > 1:
                order_id_query = '(alliance_id, alliance_name,  player_1_id, '
                player_id_query = str(ctx.author.id) + "', "
                initial_alliance_names = str(ctx.author.name).lower() + "-"
                description_names = ctx.author.name + ', '

                for index, player_id in enumerate(alliance_members):
                    order_id_query = order_id_query + 'player_' + str(index + 2) + '_id, '
                    player_id_query = player_id_query + "'" + str(player_id) + "', "
                    initial_alliance_names = initial_alliance_names + args[index].lower() + '-'
                    description_names = description_names + args[index] + ', '

                order_id_query = order_id_query[:-2] + ')'
                player_id_query = player_id_query[:-2] + ')'
                initial_alliance_names = initial_alliance_names[:-1]
                description_names = description_names[:-2]

                description = description_names + " | Requested by " + str(ctx.author.name) + " | Made on " + str(datetime.date.today())

                #try:
                if len(set(alliance_members)) == len(alliance_members):
                    alliance = await ctx.guild.create_text_channel(initial_alliance_names, category=alliance_category, topic=description)
                    await alliance.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False)
                    await alliance.set_permissions(ctx.author, read_messages=True, send_messages=True)
                    await alliance.set_permissions(spectator_role, read_messages=True, send_messages=False)

                    for player_id in alliance_members:
                        player = await ctx.guild.fetch_member(player_id)
                        await alliance.set_permissions(player, read_messages=True, send_messages=True)

                    player_id_query = "('" + str(alliance.id) + "', '" + initial_alliance_names + "', '"+  player_id_query

                    conn.execute('INSERT INTO xbot.alliances ' + order_id_query + ' VALUES ' + player_id_query)
                else:
                    await ctx.send(ctx.author.mention + ", your alliance has a repeating player!")
                #except:
                #   await ctx.send(ctx.author.mention + ", there was a problem recording this alliance.")
            else:
                await ctx.send(ctx.author.mention + ", there are not enough players in this alliance.")
        
    @commands.command()
    async def name_alliance(self, ctx, new_name, alliance=None):
        
        with self.engine.connect() as conn:
            if not alliance:
                potential_id = str(ctx.channel.id)
            else:
                potential_id = alliance[2:-1]
                print(potential_id)

            try:
                alliance_id = conn.execute("SELECT alliance_id FROM xbot.alliances WHERE alliance_id = '" + potential_id + "'").first()[0]
                alliance = ctx.guild.get_channel(int(alliance_id))
            except:
                await ctx.send(ctx.author.mention + ", this is not an alliance channel.")

            await alliance.edit(name=new_name)
            try:
                conn.execute("UPDATE xbot.alliances SET alliance_name = '" + new_name + "' WHERE alliance_id = '" + str(alliance.id) + "'")
            except:
                await ctx.send(ctx.author.mention + ", can't send new name to database.")   

    async def archive_alliance(self, ctx, alliance):
        pass
        #If None, archive the current alliance
        #If an ID is passed, archive that alliance



async def setup(bot):
    await bot.add_cog(Alliances(bot))