from atexit import register
from email import message
from http import client
from unicodedata import category
from black import target_version_option_callback
from click import command
from discord.ext import commands
import discord
import random
import asyncio
import datetime
from discord.ui import Button, View

class Xquester(commands.Cog):
    def __init__(self, client, name='Xquester Cog'):
        self.game_started = False
        self.client = client
        self.votes = {}
        self.player_count = 0
        self.room_capacity = 0
        self.players = []
        self.jury = []
        self.limit = -1
        self.player_role = None
        self.jury_role = None
        self.category = None
        self.jury_category = None
        self.confessionals = None
        self.submissions = None
        self.announcements = None
        self.register_channel = None
        self.question_channel = None
        self.jury_channel = None
        self.rooms_created = False
        self.timer_channel = None
        self.timer_message = None
        self.time = None
        # Room -> int(capacity)
        self.rooms = {}
        # Room -> Role
        self.room_roles = {}
        # Role -> Room
        self.role_rooms = {}
        # Role -> [Players]
        self.player_room_roles = {}
        self.player_submissions = {}
        self.player_confessionals = {}
        self.jury_submissions = {}
        self.player_votes = {}
        self.winner_votes = {}
        self.pause = False
        self.timer_message = None
        self.time_left = 0
        self.admin = None
        self.vote_panels = {}

    @commands.command()
    async def create_game(self, ctx, limit):
        guild = ctx.guild

        self.admin = ctx.message.author
        self.game_started = True

        self.limit = int(limit)
        self.player_role = await guild.create_role(name="Player")
        self.jury_role = await guild.create_role(name="Jury")

        self.category = await guild.create_category("Xquester")
        self.jury_category = await guild.create_category("Jury")
        self.confessionals = await guild.create_category("Confessionals")
        self.submissions = await guild.create_category("Submissions")

        self.announcements = await guild.create_text_channel("announcements", category=self.category)
        self.register_channel = await guild.create_text_channel("register", category=self.category)

        self.jury_channel = await guild.create_text_channel("jury", category=self.jury_category)

        await self.announcements.set_permissions(ctx.guild.default_role, read_messages=True, send_messages=False)
        await self.announcements.set_permissions(self.player_role, read_messages=True, send_messages=False)
        await self.register_channel.set_permissions(self.player_role, send_messages=True, read_messages=True)
        await self.confessionals.set_permissions(ctx.guild.default_role, read_messages=True, send_messages=False)
        await self.confessionals.set_permissions(self.player_role, read_messages=False, send_messages=False)
        await self.submissions.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False)
        await self.submissions.set_permissions(self.player_role, read_messages=False, send_messages=False)
        await self.jury_channel.set_permissions(self.jury_role, read_messages=True, send_messages=True)
        await self.jury_channel.set_permissions(self.player_role, read_messages=False, send_messages=False)

    @commands.command()
    async def register(self, ctx, nickname=None):
        player = ctx.message.author
        guild = ctx.guild

        if self.player_count < self.limit and self.game_started and ctx.channel.id == self.register_channel.id:
            await player.add_roles(self.player_role)
            self.players.append(player)
            self.player_count += 1

            confessional_channel = await guild.create_text_channel(player.name + "-confessional", category=self.confessionals)
            await confessional_channel.set_permissions(guild.default_role, send_messages=False)
            await confessional_channel.set_permissions(player, read_messages=True, send_messages=True)
            await confessional_channel.set_permissions(self.player_role, read_messages=False, send_messages=False)
            await confessional_channel.set_permissions(self.jury_role, read_messages=False, send_messages=False)

            submissions_channel = await guild.create_text_channel(player.name + "-submissions", category=self.submissions)
            await submissions_channel.set_permissions(player, read_messages=True, send_messages=True) 

            self.player_confessionals[player] = confessional_channel
            self.player_submissions[player] = submissions_channel
            self.player_votes[player] = None

            await ctx.send(ctx.message.author.mention + ", you have been registered!")
            await confessional_channel.send("**" + ctx.message.author.mention + ", this is your confessional channel! Here, you can record your thoughts throughout the game should you so choose. Spectators can see this channel as well!**")
            await submissions_channel.send("**" + ctx.message.author.mention + ", this is your submissions channel! This is the channel where you will send votes and do other game actions. This channel is private to yourself and the hosting team.**")
        elif not self.game_started:
            await ctx.send("The game hasn't even started yet!")
        elif ctx.channel.id != self.register_channel.id:
            await ctx.send("You cannot register here.")
        else:
            await ctx.send("Registration has ended. Try again next time!")

        if self.player_count >= self.limit:
            await ctx.send("**Registration has ended. Try again next time!**")
            await self.register_channel.set_permissions(self.player_role, send_messages=False)

    @commands.command()
    async def create_rooms(self, ctx, room_count, room_capacity, time):
        if ctx.message.author == self.admin:
            await self.announcements.send("__--------------------__")
            await self.announcements.send("**ROOM COUNT:** " + room_count)
            await self.announcements.send("**ROOM CAPACITY:** " + room_capacity)
            await self.announcements.send("**TIME:** " + str(datetime.timedelta(seconds=int(time))))
            await self.announcements.send("__--------------------__")
            await asyncio.sleep(10)
            await self.announcements.send("Rooms will open shortly.")

            room_count = int(room_count)
            room_capacity = int(room_capacity)

            self.room_capacity = room_capacity

            if self.game_started and room_capacity * room_count >= self.player_count:
                guild = ctx.guild

                for i in range(room_count):
                    room_role = await guild.create_role(name="Room " + str(i + 1))
                    room = await guild.create_text_channel("room-" + str(i + 1), category=self.category) 
                    await room.set_permissions(ctx.guild.default_role, send_messages=False)
                    await room.set_permissions(self.player_role, read_messages=False, send_messages=False)
                    await room.set_permissions(room_role, read_messages=True, send_messages=True, read_message_history=False)
                    await room.set_permissions(self.jury_role, read_messages=False, send_messages=False)

                    self.room_roles[room] = room_role
                    self.role_rooms[room_role] = room
                    self.player_room_roles[room_role] = []
                    self.rooms[room] = 0


                indexes = [i for i in range(self.player_count)]

                while indexes != []:
                    
                    room_selection = random.choice(list(self.rooms.keys()))

                    if self.rooms[room_selection] < room_capacity:
                        self.rooms[room_selection] += 1

                        player_selection = self.players[indexes.pop(random.randrange(len(indexes)))]
                        await player_selection.add_roles(self.room_roles[room_selection])

                        self.player_room_roles[self.room_roles[room_selection]].append(player_selection)

                self.rooms_created = True

                message = f"{self.player_role.mention}s, the countdown has ended! Rooms are now closing."

                await self.announcements.send(self.player_role.mention + ", begin play.")
                await self.start_timer(ctx, time, message)
            elif room_capacity * room_count < self.player_count:
                await ctx.send("You cannot create rooms with those constraints.")
            else:
                await ctx.send("No game in progress.")
        else:
            await ctx.send('You may not perform this action.')


    @commands.command()
    async def move(self, ctx, room_number):
        if ctx.message.author in self.players:
            player = ctx.message.author

            origin_room = ctx.channel
            origin_role = self.room_roles[origin_room]

            for dest_role in self.room_roles.values():
                if dest_role.name == "Room " + room_number:

                    dest_room = self.role_rooms[dest_role]

                    if self.rooms_created and self.rooms[dest_room] < self.room_capacity:
                        await player.remove_roles(origin_role)
                        await player.add_roles(dest_role)
                        self.player_room_roles[origin_role].remove(player)
                        self.player_room_roles[dest_role].append(player)
                        self.rooms[origin_room] -= 1
                        self.rooms[dest_room] += 1   
                        await origin_room.send(player.mention + " has left the room.")
                        await dest_room.send(player.mention + " has entered the room.")


                    elif self.rooms[dest_room] >= self.room_capacity:
                        await ctx.send("This room is at room limit! Use ```-status``` to find an empty room.")
                    else:
                        await ctx.send("Rooms have not been created yet.")
                    
                    return

            await ctx.send("Room not found. Ensure that you typed in a room that exists using the ```-status``` command.")
        else:
            await ctx.send('You are not a player. You cannot perform this action.')

    @commands.command()
    async def start_game(self, ctx):
        await self.announcements.send(self.player_role.mention)
        await self.announcements.send("**--- Welcome to X-Quester ---**")
        await self.announcements.send("https://media.discordapp.net/attachments/1007796742797926582/1007797326884126772/xquesterlogo.png")
        await asyncio.sleep(2)
        await self.announcements.send("**__Please pay close attention to following information__**")
        await asyncio.sleep(5)
        await self.announcements.send(
            '''
            You are about to play X-Quester. A first of it's kind gamemode that intergrates Sequester-Minis with Discord.\nIf you are not aware of what a Sequester-Mini is, think of it like a Mini version of Survivor! (Challenges, voteouts, etc.)
            
            '''

        )
        await asyncio.sleep(15)

        await self.announcements.send("__**How this works:**__")
        await asyncio.sleep(10)
        await self.announcements.send("- The game will be broken up into rounds. At the end of each round, 1 or more players will be eliminated from the game.")
        await asyncio.sleep(10)
        await self.announcements.send("- Every round will be timed, the exact amount of time to be announced at the beginning of the round by the Main Host.")
        await asyncio.sleep(10)
        await self.announcements.send("- The round usually starts with **free time**. During this, you will move between a certain number of \"rooms\" which are text channels. You are confined to that text channel room until you decide to move to another one.")
        await asyncio.sleep(10)
        await self.announcements.send("- Each room has a room limit, only a certain number of people can be in a room at a time.")
        await asyncio.sleep(10)
        await self.announcements.send("- In these rooms you can discuss anything and everything with the other players in your room.")
        await asyncio.sleep(10)
        await self.announcements.send("- Sequester-Minis are often played on VCs. In order to simulate this environment, **read history between rooms has been disabled, similar to walking in on a VC room.**")
        await asyncio.sleep(10)
        await self.announcements.send("- Once free time ends, the rooms will close and the voting phase will begin.")
        await asyncio.sleep(10)
        await self.announcements.send("- You will have a specified amount of time to **vote** in your **submissions** channel for any players you wish including yourself.")
        await asyncio.sleep(10)
        await self.announcements.send("- Each voting round will have a twist that will be annouced at the beginning of free time. For example: the person with the lowest or highest amount of votes goes home, etc.")
        await asyncio.sleep(10)
        await self.announcements.send("- These twists are entirely random and will fundamentally shift the way subsequent rounds are played.")
        await asyncio.sleep(10)
        await self.announcements.send("- Play will continue until there are 2 players remaining, where players must then convince their a jury of the eliminated players to vote them to win.")
        await asyncio.sleep(10)
        await self.announcements.send("__**How to play**__")
        await asyncio.sleep(10)
        await self.announcements.send("X-Quester is almost entirely run by me, X-BOT. I will perform most of the functions required to play the game.")
        await asyncio.sleep(10)
        await self.announcements.send("You can see all the important commands you may need by typing ```-explain```")
        await asyncio.sleep(10)
        await self.announcements.send("To see a list of all the players in the game, type ```-see_players```")
        await asyncio.sleep(10)
        await self.announcements.send("To see where players currently are in each room or to check room limit, type ```-status```")
        await asyncio.sleep(10)
        await self.announcements.send("**You can only move between rooms *in* said rooms, you can only vote in your submissions.**")
        await asyncio.sleep(10)
        await self.announcements.send("**If you have any other questions, please ping the Main Host.**")
        await asyncio.sleep(10)
        await self.announcements.send("**X-Quester will begin shortly.**")




    @commands.command()
    async def status(self, ctx):
        if self.rooms_created:
            message = ""

            for role in self.player_room_roles.keys():
                message = message +  "\n**__" + role.name + ":__**  "
                for player in self.player_room_roles[role]:
                    message = message + player.name + ", "
                message = message[:-2]
                message = message + "\n" + str(len(self.player_room_roles[role])) + "/" + str(self.room_capacity) 

            await ctx.send(message)
        else:
            await ctx.send("There are currently no rooms.")
        
    @commands.command()
    async def delete_all(self, ctx):
        if ctx.message.author == self.admin:
            for room in self.rooms.keys():
                await room.delete()

            for role in self.room_roles.values():
                await role.delete()

            for confessional in self.player_confessionals.values():
                await confessional.delete()
            
            for submission in self.player_submissions.values():
                await submission.delete()

            for submission in self.jury_submissions.values():
                await submission.delete()

            await self.jury_channel.delete()

            await self.jury_category.delete()

            await self.jury_role.delete()

            await self.player_role.delete()

            await self.register_channel.delete()


            await self.announcements.delete()

            await self.category.delete()

            await self.submissions.delete()

            await self.confessionals.delete()


    @commands.command()
    async def end_rooms(self, ctx):
        if ctx.message.author == self.admin:
            if self.rooms_created:
                for room in self.rooms.keys():
                    await room.delete()

                for role in self.room_roles.values():
                    await role.delete()

                self.rooms_created = False
                self.rooms = {}
                self.room_roles = {}
                self.role_rooms = {}
                self.player_room_roles = {}
            else:
                await ctx.send("Rooms have not been created yet.")
            

    @commands.command()
    async def start_timer(self, ctx, time_input, end_message=None, jury_time=False, regular_vote=True):
        #Code adapted from: https://stackoverflow.com/questions/64150736/how-to-make-a-timer-command-in-discord-py
        if ctx.message.author == self.admin:
            try:
                try:
                    self.time = int(time_input)
                except:
                    convertTimeList = {'s':1, 'm':60, 'h':3600, 'd':86400, 'S':1, 'M':60, 'H':3600, 'D':86400}
                    self.time = int(time_input[:-1]) * convertTimeList[time_input[-1]]
                if self.time > 86400:
                    await ctx.send("Please enter a value less than 24 hours.")
                    return
                if self.time <= 0:
                    await ctx.send("Please enter a non-negative value.")
                    return

                if self.time >= 3600:
                    time_message = f"Timer: {self.time//3600}:{self.time%3600//60}:{self.time%60}"
                    self.timer_message = await self.announcements.send(time_message)
                elif self.time >= 60:
                    time_message = f"Timer: {self.time//60}:{self.time%60}"
                    self.timer_message = await self.announcements.send(time_message)
                elif self.time < 60:
                    time_message = f"Timer: {self.time}"
                    self.timer_message = await self.announcements.send(time_message)


                while True:
                    if not self.pause:
                        await asyncio.sleep(1)
                        self.time -= 1
                        if self.time >= 3600:
                            await self.timer_message.edit(content=f"Timer: {self.time//3600}:{self.time %3600//60}:{self.time%60}")
                        elif self.time >= 60:
                            await self.timer_message.edit(content=f"Timer: {self.time//60}:{self.time%60}")
                        elif self.time > 0:
                            await self.timer_message.edit(content=f"Timer: {self.time}")
                        elif self.time <= 0:
                            await self.timer_message.edit(content=f"Timer: {self.time}")
                            if end_message:
                                await self.announcements.send(end_message)
                            else:
                                await self.announcements.send(self.player_role.mention + ", time is up! The rooms will now close.")
                            await asyncio.sleep(10)
                            if jury_time:
                                if self.jury:
                                    await asyncio.sleep(10)
                                    await self.question_channel.set_permissions(self.jury[0], read_messages=True, send_messages=False)
                                    self.jury.pop(0)
                                    if self.jury:
                                        await self.announcements.send(self.jury[0].mention + ", your questioning may begin.")
                                        await self.question_channel.set_permissions(self.jury[0], read_messages=True, send_messages=True)
                                        await self.start_timer(ctx, 120, self.jury[0].mention + ", your questioning has concluded.", jury_time=True, regular_vote=False)
                                    else:
                                        await self.announcements.send("Questioning has concluded. " 
                                            + self.jury_role.mention
                                            + "You have 3 minutes to submit your votes to your submissions.")
                                        await self.start_timer(ctx, 180, self.jury_role.mention 
                                        + " and " 
                                        + self.player_role.mention 
                                        + ",**voting has concluded and a winner has been chosen. The Main Host will now annouce the results.**"
                                        , regular_vote=False)
                            else:
                                if self.rooms_created:
                                    await self.end_rooms(ctx)
                                    self.rooms_created = False
                                if regular_vote:
                                    await self.announcements.send(self.player_role.mention + "s, you have 2 minutes to vote for a player in your submissions.")
                                    await asyncio.sleep(10)
                                    await self.start_timer(ctx, 120, self.player_role.mention + "s, voting has finished.", regular_vote=False)
                            return
                    else:
                        self.time = self.time
            except:
                await ctx.send(f"Please input a valid time in seconds.")

    @commands.command()
    async def pause(self, ctx):
        if ctx.message.author == self.admin:
            self.pause = True

    @commands.command()
    async def resume(self, ctx):
        if ctx.message.author == self.admin:
            if self.pause:
                self.pause = False
                await self.start_timer(ctx, self.time, self.timer_message)

    @commands.command()
    async def vote(self, ctx, name):
        if ctx.message.author in self.players:
            voter = ctx.message.author

            for submission_channel in self.player_submissions.values():
                if submission_channel.id == ctx.channel.id:
                    for vote_candidate in self.players:
                        if vote_candidate.name == name:
                            self.player_votes[voter] = vote_candidate
                            await ctx.send("**You have voted for " + vote_candidate.name + "**")
                            return
                    
                    await ctx.send("Player not found. Please ensure that you spelled the player's name correctly. See a full list of names with ```-see_players```Use quotes (Ex. -vote \"My Name\") to vote for someone with spaces in their name.")
                    return
            
            await ctx.send("You cannot send votes here! Looks for your submissions channel below.")
        else:
            ctx.send('You are not a player. You cannot perform this action.')

    @commands.command()
    async def vote_winner(self, ctx, name):
        if ctx.message.author in self.jury_submissions.keys():
            voter = ctx.message.author

            for submission_channel in self.jury_submissions.values():
                if submission_channel.id == ctx.channel.id:
                    for vote_candidate in self.players:
                        if vote_candidate.name == name:
                            self.winner_votes[voter] = vote_candidate
                            await ctx.send("**You have voted for " + vote_candidate.name + "**")
                            await ctx.author.send("**Thank you so much for playing X-Quester!**\n\nWe are so happy you decided to give us a try, and we would love to hear about your experience! Attached below is a survey, if you have a spare moment and would like to contribute to the further development of X-Quester, please consider filling it out.\n\nOn behalf of XTRON and myself, thank you again!\n\nhttps://forms.gle/M3pph6XXE5tWzpoX8")
                            return
                    
                    await ctx.send("Player not found. Please ensure that you spelled the player's name correctly. See a full list of names with ```-see_players```Use quotes (Ex. -vote \"My Name\") to vote for someone with spaces in their name.")
                    return
            
            await ctx.send("You cannot send votes here! Looks for your submissions channel below.")
        else:
            await ctx.send('You are not a member of the jury. You cannot perform this action.')
        

    
    @commands.command()
    async def see_votes(self, ctx, winner=False):
        if ctx.message.author == self.admin:
            counts = {}
            message = ""

            if winner:
                votes = self.winner_votes
            else:
                votes = self.player_votes

            for player in votes.keys():
                if votes[player]:
                    message += player.name + ": *" + votes[player].name + "*\n"
                    if votes[player] in counts.keys():
                        counts[votes[player]] += 1
                    else:
                        counts[votes[player]] = 1
                else:
                    message += player.name + ": **Not voted**\n"

            message += "\n------Vote Count Summary------\n"

            for count in counts:
                message += "**" + count.name + ": " + str(counts[count]) + "**\n"

            await ctx.send(message)

    @commands.command()
    async def flush_votes(self, ctx):
        if ctx.message.author == self.admin:
            for player in self.player_votes.keys():
                self.player_votes[player] = None

    @commands.command()
    async def see_players(self, ctx):
        message = "__------List of Players------__\n"
        for player in self.players:
            message += player.name + "\n"

        await ctx.send(message)

    @commands.command()
    async def insert_player(self, ctx, name, room_number):

        for player in self.players:
                if player.name == name:
                    for dest_role in self.room_roles.values():
                        if dest_role.name == "Room " + room_number:

                            dest_room = self.role_rooms[dest_role]

                            if self.rooms_created and self.rooms[dest_room] < self.room_capacity:
                                await player.add_roles(dest_role)
                                self.player_room_roles[dest_role].append(player)
                                self.rooms[dest_room] += 1   
                                await dest_room.send(player.mention + " has entered the room.")


                            elif self.rooms[dest_room] >= self.room_capacity:
                                await ctx.send("This room is at room limit! Use ```-status``` to find an empty room.")

                            else:
                                await ctx.send("The rooms haven't been created yet.")

                    await ctx.send("Room not found. Ensure that you typed in a room that exists using the ```-status``` command.")
                    return
        await ctx.send('Player not found.')
        return
                            


    @commands.command()
    async def remove_player(self, ctx, name, complete=False, jury=False):
        if ctx.message.author == self.admin:
            for player in self.players:
                if player.name == name:
                    if jury == True:
                        await player.add_roles(self.jury_role)      
                        self.jury.append(player)   
                        self.jury_submissions[player] = self.player_submissions[player]  
                    
                    if jury == False and complete == False:
                        await player.send("**Thank you so much for playing X-Quester!**\n\nWe are so happy you decided to give us a try, and we would love to hear about your experience! Attached below is a survey, if you have a spare moment and would like to contribute to the further development of X-Quester, please consider filling it out.\n\nOn behalf of XTRON and myself, thank you again!\n\nhttps://forms.gle/M3pph6XXE5tWzpoX8")

                    if complete == True:
                        self.player_confessionals[player].delete()
                        self.player_submissions[player].delete()

                    self.players.remove(player)
                    self.player_votes.pop(player)
                    self.player_count -= 1      

                    self.player_confessionals.pop(player)
                    self.player_submissions.pop(player)
                    await player.remove_roles(self.player_role)
                    await self.flush_votes(ctx)
    
    @commands.command()
    async def explain(self, ctx):
        message = '''**-move {room number}    |   Move to a new room**
**-see_players                        |   See all the players currently in the game**
**-status                                   |   See which players are in each room**
**-vote_panel                |   Request a vote panel (done in submissions)**'''
        await ctx.send(message)

    @commands.command()
    async def rocks(self, ctx, exempt_players):
        if ctx.message.author == self.admin:
            await ctx.send("**__Beginning Rocks:__**")
            rock_players = self.players.copy()
            for player in exempt_players:
                rock_players.pop(player)

            while len(rock_players) != 1:
                await asyncio.sleep(3)
                await ctx.send(".")
                await asyncio.sleep(3)
                await ctx.send(".")
                await asyncio.sleep(3)
                await ctx.send(".")
                player = rock_players.pop(random.randrange(len(rock_players)))
                await ctx.send("**" + player.mention + " is safe.**")
        
            await ctx.send("**" + rock_players[0].mention + " has been eliminated.**")
        else:
            await ctx.send("You may not perform this action.")

    @commands.command()
    async def explain_voting(self, ctx):
        if ctx.message.author == self.admin:
            for player in self.players:
                await self.player_submissions[player].send(player.mention + "**, it is time to vote!**\n\n You may request a voting panel by typing **-vote_panel**")


    @commands.command()
    async def vote_panel(self, ctx):
        for submission_channel in self.player_submissions.values():
                if submission_channel.id == ctx.channel.id:

                    voter = ctx.message.author

                    embed=discord.Embed(title="Vote Panel", description="**Click the button the player you wish to vote**")
                    embed.set_thumbnail(url="https://media.discordapp.net/attachments/797674938298662963/1027730360068481144/XQuesterIcon.png")

                    self.vote_panels[voter] = {}

                    await ctx.send(embed=embed)

                    for player in self.players:
                        view = View()
                        button = Button(label=player.name, style=discord.ButtonStyle.primary)
                        view.add_item(button)
                        msg = await ctx.send(view=view)
                        self.vote_panels[voter][msg] = player

                    while True:
                        selected_button = await self.client.wait_for("interaction")
                        vote_candidate = self.vote_panels[voter][selected_button.message]
                        if vote_candidate in self.players:
                            self.player_votes[voter] = vote_candidate
                            await selected_button.response.send_message("**You have voted for " + vote_candidate.name + "**")
                        else:
                            await selected_button.response.send_message("**This player is no longer in the game.**")

    @commands.command()
    async def assign_partners(self, ctx, title):
        if ctx.message.author == self.admin and len(self.players) % 2 == 0:
            potential_partners = self.players.copy()

            while potential_partners:
                partner_1 = potential_partners.pop(random.randrange(len(potential_partners)))
                partner_2 = potential_partners.pop(random.randrange(len(potential_partners)))

                await self.player_submissions[partner_1].send(partner_1.mention + ", your " + title + " is " + partner_2.mention)
                await self.player_submissions[partner_2].send(partner_2.mention + ", your " + title + " is " + partner_1.mention)
        elif len(self.players) % 2 != 0:
            await ctx.send("There is not an even number of players")
        else:
            await ctx.send("You may not perform this action.")

    @commands.command()
    async def assign_target(self, ctx, title):
        if ctx.message.author == self.admin and len(self.players) % 2 == 0:
            potential_targets = self.players.copy()

            for player in self.players:
                target = potential_targets.pop(random.randrange(len(potential_targets)))
                while target == player:
                    target = potential_targets.pop(random.randrange(len(potential_targets)))

                await self.player_submissions[player].send(player.mention + ", your " + title + " is " + target.mention)
        else:
            await ctx.send("You may not perform this action.")


    @commands.command()
    async def begin_jury(self, ctx):
        guild = ctx.guild
        await self.announcements.send('**Welcome to the Final Vote.**')
        speech_channel = await guild.create_text_channel("speeches", category=self.jury_category)
        self.question_channel = await guild.create_text_channel("jury-questioning", category=self.jury_category)

        await self.question_channel.set_permissions(self.jury_role, read_messages=True, send_messages=False)  
        await speech_channel.set_permissions(self.jury_role, read_messages=True, send_messages=False)

        await asyncio.sleep(3)


        await self.announcements.send('**Finalists' 
            + self.players[0].mention 
            + 'and' + self.players[-1].mention 
            + ', you now have 4 minutes to compose and present an opening speech. Then place them in the <#' 
            + str(speech_channel.id) + '>**')

        await asyncio.sleep(10)
        await self.start_timer(ctx, 240, self.player_role.mention + ", opening speeches have concluded.")

        await self.announcements.send('**Finalists will now begin questioning with the ' 
        + self.jury_role.mention 
        + '. Each jury member will have 2 minutes to question the Finalists in <#' 
        + str(self.question_channel.id) 
        + '>. Jurors will have until the end of questioning and an additional 5 minutes to submit their final votes to their submissions channel.**')

        await asyncio.sleep(10)

        await self.announcements.send('**We will begin with ' + self.jury[0].mention + '.**')

        await asyncio.sleep(5)

        await self.question_channel.set_permissions(self.jury[0], read_messages=True, send_messages=True)
        await self.question_channel.set_permissions(self.player_role, read_messages=True, send_messages=True)

        await self.start_timer(ctx, 120, self.jury[0].mention + ", your questioning has concluded.", jury_time=True, regular_vote=False)


    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        print(err)

async def setup(bot):
    await bot.add_cog(Xquester(bot))



    
