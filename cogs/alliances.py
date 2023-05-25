import sqlalchemy
from discord.ext import commands
import discord
import random
import asyncio
from datetime import datetime
from discord.ui import Button, View
import os
import pandas as pd
import matplotlib.pyplot as plt
import dataframe_image as dfi
import numpy as np
import re

class Alliances(commands.Cog):
    def __init__(self, client, name='Specgames Cog'):
        self.engine = sqlalchemy.create_engine( "mysql+pymysql://" + os.getenv('SQL_USERNAME') + ":" + os.getenv('SQL_PASSWORD') + "@127.0.0.1/xbot")


    async def get_alliance(self, conn, ctx, alliance=None):
        if not alliance:
            potential_id = str(ctx.channel.id)
        else:
            potential_id = alliance[2:-1]

        try:
            alliance_id = conn.execute("SELECT alliance_id FROM xbot.alliances WHERE alliance_id = '" + potential_id + "'").first()[0]
            alliance = ctx.guild.get_channel(int(alliance_id))
        except:
            await ctx.send(ctx.author.mention + ", this is not an alliance channel.")
        
        return alliance
    
    async def get_alliance_member_ids(self, conn, ctx, alliance):
        try:
            alliance_member_ids = conn.execute("SELECT player_list FROM xbot.alliances WHERE alliance_id = '" + str(alliance.id) + "'").first()[0]
        except:
            await ctx.send(ctx.author.mention + ", this is not an alliance channel.")
        
        return alliance_member_ids.split("-")
    
    async def get_category(self, conn, ctx, name):
        try:
            category_query = conn.execute("SELECT category_id FROM xbot.categories WHERE category_name = '" + name + "'")
            category_id = category_query.fetchone()[0]
            category = next(item for item in ctx.guild.categories if item.id == int(category_id))
        except:
            await ctx.send(ctx.author.mention + ", no " + name + " category has been set up.")
            return
        
        return category
    
    async def get_player_id_by_name(self, conn, ctx, player_name):
        try:
            player = conn.execute("SELECT player_id FROM xbot.players WHERE player_name = '" + player_name + "'").first()[0]
        except:
            await ctx.send(ctx.author.mention + ", one of these players is not found. Please check your list again for proper spelling.")
            return
        
        return player
    
    async def get_spectator_role(self, conn, ctx):
        try:
            spectator_id = conn.execute("SELECT role_id FROM xbot.roles WHERE role_type = 'Spectators'").first()[0]
            spectator_role = ctx.guild.get_role(int(spectator_id))
        except:
            await ctx.send(ctx.author.mention + ", no spectator role has been set up.")
            return
        
        return spectator_role
    
    async def duplicate_alliance_check(self, conn, ctx):
        try:
            spectator_id = conn.execute("SELECT alliance_id, creation_date COUNT(*) FROM users GROUP BY name, email HAVING COUNT(*) > 1").first()[0]
            spectator_role = ctx.guild.get_role(int(spectator_id))
        except:
            await ctx.send(ctx.author.mention + ", no spectator role has been set up.")
            return
        
        return spectator_role


    @commands.command()
    async def create_alliance(self, ctx, *args):
        with self.engine.connect() as conn:

            alliance_members = []
            spectator_role = None

            alliance_category = await self.get_category(conn, ctx, "Alliances")
            spectator_role = await self.get_spectator_role(conn, ctx)
            
            for player_name in args:
                alliance_members.append(await self.get_player_id_by_name(conn, ctx, player_name))

            if len(alliance_members) > 1:
                order_id_query = '(alliance_id, alliance_name, player_list, creation_date)'
                player_id_query = str(ctx.author.id) + "-"
                initial_alliance_names = str(ctx.author.name).lower() + "-"
                description_names = ctx.author.name + ', '

                for index, player_id in enumerate(alliance_members):
                    player_id_query = player_id_query + str(player_id) + "-"
                    initial_alliance_names = initial_alliance_names + args[index].lower() + '-'
                    description_names = description_names + args[index] + ', '

                player_id_query = player_id_query[:-1]
                initial_alliance_names = initial_alliance_names[:-1]
                description_names = description_names[:-2]

                description = description_names + " | Requested by " + str(ctx.author.name) + " | Made on " + str(datetime.today())

                try:
                    if len(set(alliance_members)) == len(alliance_members):
                        alliance = await ctx.guild.create_text_channel(initial_alliance_names, category=alliance_category, topic=description)
                        await alliance.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False)
                        await alliance.set_permissions(ctx.author, read_messages=True, send_messages=True)
                        await alliance.set_permissions(spectator_role, read_messages=True, send_messages=False)

                        for player_id in alliance_members:
                            player = await ctx.guild.fetch_member(player_id)
                            await alliance.set_permissions(player, read_messages=True, send_messages=True)

                        player_id_query = "('" + str(alliance.id) + "', '" + initial_alliance_names + "', '" +   player_id_query + "', '" + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "')"

                        conn.execute('INSERT INTO xbot.alliances ' + order_id_query + ' VALUES ' + player_id_query)
                    else:
                        await ctx.send(ctx.author.mention + ", your alliance has a repeating player!")
                except:
                    await ctx.send(ctx.author.mention + ", there was a problem recording this alliance.")
            else:
                await ctx.send(ctx.author.mention + ", there are not enough players in this alliance.")
        
    @commands.command()
    async def rename_alliance(self, ctx, new_name, alliance=None):
        with self.engine.connect() as conn:
            alliance = await self.get_alliance(conn, ctx, alliance)

            await alliance.edit(name=new_name)

            try:
                conn.execute("UPDATE xbot.alliances SET alliance_name = '" + new_name + "' WHERE alliance_id = '" + str(alliance.id) + "'")
            except:
                await ctx.send(ctx.author.mention + ", can't send new name to database.")   

    @commands.command()
    async def archive_alliance(self, ctx, alliance=None):
        with self.engine.connect() as conn:
            alliance_category = await self.get_category(conn, ctx, "Archived Alliances")
            alliance = await self.get_alliance(conn, ctx, alliance)
            alliance_members = await self.get_alliance_member_ids(conn, ctx, alliance)

            for player_id in alliance_members:
                player = await ctx.guild.fetch_member(player_id)
                await alliance.set_permissions(player, read_messages=True, send_messages=False)

            await alliance.edit(category=alliance_category)
            await alliance.send("Alliance archived.")

    @commands.command()
    async def remove_player_from_alliance(self, ctx, player_name, alliance=None):
        pass_alliance = alliance
        with self.engine.connect() as conn:
            alliance = await self.get_alliance(conn, ctx, alliance)
            alliance_members = await self.get_alliance_member_ids(conn, ctx, alliance)
            player_id = await self.get_player_id_by_name(conn, ctx, player_name)
            player = await ctx.guild.fetch_member(player_id)

            if player_id in alliance_members:
                    
                alliance_members.remove(player_id)
                new_player_list = '-'.join(alliance_members)

                await alliance.set_permissions(player, read_messages=False, send_messages=False)

                match = re.search(player_name, alliance.topic)
                new_topic = alliance.topic[:match.start()] + "~~" + alliance.topic[match.start():match.end()] + "~~" + alliance.topic[match.end():]
                await alliance.edit(topic=new_topic)
                
                try:
                    conn.execute("UPDATE xbot.alliances SET player_list = '" + new_player_list + "' WHERE alliance_id = " + str(alliance.id))
                except:
                   await ctx.send(ctx.author.mention + ", this player cannot be removed from our database.")    

                await ctx.send(player_name + " removed.")

                if len(alliance_members) < 3:
                    await self.archive_alliance(ctx, pass_alliance)
            else:
                await ctx.send(ctx.author.mention + ', this player in not in this alliance.')



async def setup(bot):
    await bot.add_cog(Alliances(bot))