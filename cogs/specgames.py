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

class Specgames(commands.Cog):
    def __init__(self, client, name='Specgames Cog'):
        self.engine = sqlalchemy.create_engine( "mysql+pymysql://" + os.getenv('SQL_USERNAME') + ":" + os.getenv('SQL_PASSWORD') + "@127.0.0.1/xbot")

    @commands.command()
    async def add_player(self, ctx, player_name):
        with self.engine.connect() as conn:
            conn.execute("INSERT INTO xbot.players (player_name) VALUES ('" + player_name + "')")
            await ctx.send("Player added.")

        
    @commands.command()
    async def add_draft(self, ctx, winner_pick, pick_1, pick_2, pick_3):
        with self.engine.connect() as conn:

            try:
                conn.execute("INSERT INTO xbot.spectators (spectator_id, spectator_name) VALUES ('" + str(ctx.author.id) + "', '" + ctx.author.name + "')")
            except:
                pass

            try:
                winner_id = conn.execute("SELECT player_id FROM xbot.players WHERE player_name = '" + winner_pick + "'").first()[0]
                pick_1_id = conn.execute("SELECT player_id FROM xbot.players WHERE player_name = '" + pick_1 + "'").first()[0]
                pick_2_id = conn.execute("SELECT player_id FROM xbot.players WHERE player_name = '" + pick_2 + "'").first()[0]
                pick_3_id = conn.execute("SELECT player_id FROM xbot.players WHERE player_name = '" + pick_3 + "'").first()[0]
            except:
                await ctx.send(ctx.author.mention + ", one of these players is not found. Please check your draft picks.")
                return

            spectator_id = ctx.author.id
            draft = [winner_id, pick_1_id, pick_2_id, pick_3_id]

            try:
                if len(set(draft)) == len(draft):
                    conn.execute(
                        "INSERT INTO xbot.draft (spectator_id, winner_pick_id, pick_1_id, pick_2_id, pick_3_id) VALUES ('{spectator_id}', '{winner_pick}', '{pick_1}', '{pick_2}', '{pick_3}')"
                        .format(spectator_id=spectator_id, winner_pick=winner_id, pick_1=pick_1_id, pick_2=pick_2_id, pick_3=pick_3_id)
                    )
                    await ctx.send(ctx.author.mention + ", your draft has been added!")
                else:
                    await ctx.send(ctx.author.mention + ", your draft has a repeating player!")
            except:
                await ctx.send(ctx.author.mention + ", this draft already exists! Change some of your placements please.")

    

    @commands.command()
    async def add_bootlist(self, ctx, *args):
        with self.engine.connect() as conn:
            try:
                conn.execute("INSERT INTO xbot.spectators (spectator_id, spectator_name) VALUES ('" + str(ctx.author.id) + "', '" + ctx.author.name + "')")
            except:
                pass

            bootlist = []

            try:
                for player_name in args:
                    bootlist.append(conn.execute("SELECT player_id FROM xbot.players WHERE player_name = '" + player_name + "'").first()[0])
            except:
               await ctx.send(ctx.author.mention + ", one of these players is not found. Please check your list again for proper spelling.")
               return

            player_count = int(conn.execute("SELECT COUNT(*) FROM xbot.players").first()[0])

            if len(bootlist) < player_count:
                await ctx.send(ctx.author.mention + ", your bootlist doesn't have all the players!")
                return
            
            if len(bootlist) > player_count:
                await ctx.send(ctx.author.mention + ", your bootlist doesn't have all the players!")
                return

            pick_id_query = '(spectator_id, '
            player_id_query = "('" + str(ctx.author.id) + "', "

            for placement, player_id in enumerate(bootlist):
                pick_id_query = pick_id_query + 'pick_' + str(placement + 1) + '_id, '
                player_id_query = player_id_query + "'" + str(player_id) + "', "

            pick_id_query = pick_id_query[:-2] + ')'
            player_id_query = player_id_query[:-2] + ')'
            
            print(pick_id_query)
            print(player_id_query)

            try:
                if len(set(bootlist)) == len(bootlist):
                    conn.execute('INSERT INTO xbot.bootlist' + pick_id_query + ' VALUES ' + player_id_query)
                    await ctx.send(ctx.author.mention + ", your bootlist has been added!")
                else:
                    await ctx.send(ctx.author.mention + ", your bootlist has a repeating player!")
            except:
                await ctx.send(ctx.author.mention + ", this bootlist already exists! Change some of your placements please.")



    @commands.command()
    async def update_placements(self, ctx, player):
        with self.engine.connect() as conn:
            lowest_placement = conn.execute("SELECT MIN(placement) FROM xbot.players").first()[0]
            

            if not lowest_placement:
                highest_placement = conn.execute("SELECT COUNT(player_id) FROM xbot.players").first()[0]
                conn.execute(
                    "UPDATE xbot.players SET placement = '{highest_placement}' WHERE player_name = '{player}'"
                    .format(highest_placement=highest_placement, player=player)
                )
                await ctx.send("Placements updated.")
            elif lowest_placement == 1:
                await ctx.send("Placements have already been determined.")
            else:
                conn.execute(
                    "UPDATE xbot.players SET placement = '{lowest_placement}' WHERE player_name = '{player}'"
                    .format(lowest_placement=int(lowest_placement) - 1, player=player)
                )
                await ctx.send("Placements updated.")


    @commands.command()
    async def get_draft(self, ctx):
        with self.engine.connect() as conn:
            joined_draft = pd.read_sql("select * from (xbot.players JOIN xbot.draft AS A ON xbot.players.player_id) JOIN xbot.spectators ON A.spectator_id = xbot.spectators.spectator_id WHERE xbot.players.player_id = A.pick_1_id OR xbot.players.player_id = A.pick_2_id OR xbot.players.player_id = A.pick_3_id OR xbot.players.player_id = A.winner_pick_id ORDER BY xbot.A.spectator_id", conn)

            draft = pd.DataFrame(columns=["Spectator", "Winner Pick", "Pick 1", "Pick 2", "Pick 3", "Points"])

            row_to_be_added = [None]
            points = 0

            for index, row in joined_draft.iterrows():
                if index % 4 == 0:    
                    row_to_be_added.append(int(points))
                    if row_to_be_added[0] != None:
                        draft.loc[len(draft.index)] = row_to_be_added
                    row_to_be_added = [row['spectator_name']]
                    points = 0
                
                player = row['player_name']
                player_id = row['player_id']
                placement = row['placement']

                if pd.isna(placement):
                    placement = 0

                if player_id == row['winner_pick_id']:
                    row_to_be_added.insert(1, player)
                    points += 2 * placement
                else:
                    if player_id == row['pick_1_id']:
                        row_to_be_added.insert(2, player)
                    elif player_id == row['pick_2_id']:
                        row_to_be_added.insert(3, player)
                    else:
                        row_to_be_added.insert(4, player)
                
                    points += placement

            row_to_be_added.append(points)
            draft.loc[len(draft.index)] = row_to_be_added

            df_styled = draft.style.background_gradient()

            dfi.export(df_styled,"draft.png")

            with open('draft.png', 'rb') as f:
                picture = discord.File(f)
                await ctx.send(file=picture)
                        

    @commands.command()
    async def get_bootlist(self, ctx):
        with self.engine.connect() as conn:
            player_query = pd.read_sql("SELECT * FROM xbot.players", conn)
            spectator_query = pd.read_sql("SELECT * FROM xbot.spectators", conn)

            id_stats = player_query.set_index('player_id').to_dict('dict')
            spectators = spectator_query.set_index('spectator_id').to_dict('dict')['spectator_name']

            players = id_stats['player_name']
            placements = id_stats['placement']
            
            bootlists = pd.read_sql("SELECT * FROM xbot.bootlist", conn)
            bootlist = pd.DataFrame()
            
            def point_generator(placement, index):
                if pd.isna(placement):
                    return 'TBD'
                else:
                    return str(abs(placement - index))


            for row in bootlists.iterrows():
                points = 0
                new_bootlist = []
                for index, player_id in enumerate(row[1].items()):
                    if index == 0:
                        continue
                    if not player_id[1]:
                        break
                    
                    current_points = point_generator(placements[player_id[1]], index)

                    new_bootlist.append(players[player_id[1]] + " (" + current_points + ")")

                    if current_points != 'TBD':
                        points += int(float(current_points))

                new_bootlist.append(str(points))

                bootlist[spectators[row[1]['spectator_id']]] = new_bootlist

            bootlist.index = np.arange(1, len(bootlist) + 1)

            bootlist.rename(index={23: 'Points'}, inplace=True)

            df_styled = bootlist.style.background_gradient()

            dfi.export(df_styled,"bootlist.png")

            with open('bootlist.png', 'rb') as f:
                picture = discord.File(f)
                await ctx.send(file=picture)            



async def setup(bot):
    await bot.add_cog(Specgames(bot))