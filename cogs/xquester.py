from atexit import register
from email import message
from click import command
from discord.ext import commands
import discord
import random
import asyncio

class Xquester(commands.Cog):
    def __init__(self, client, name='Xquester Cog'):
        self.game_started = False
        self.client = client
        self.votes = {}
        self.player_count = 0
        self.room_capacity = 0
        self.players = []
        self.limit = -1
        self.player_role = None
        self.category = None
        self.submissions = None
        self.announcements = None
        self.register_channel = None
        self.rooms_created = False
        # Room -> int(capacity)
        self.rooms = {}
        # Room -> Role
        self.room_roles = {}
        # Role -> Room
        self.role_rooms = {}
        # Role -> [Players]
        self.player_room_roles = {}
        self.player_votes = {}

    @commands.command()
    async def create_game(self, ctx, limit):
        guild = ctx.guild

        self.game_started = True

        self.limit = int(limit)
        self.player_role = await guild.create_role(name="Player")

        self.category = await guild.create_category("Xquester")
        self.submissions = await guild.create_category("Submissions")
        self.announcements = await guild.create_text_channel("announcements", category=self.category)
        self.register_channel = await guild.create_text_channel("register", category=self.category)

        await self.announcements.set_permissions(ctx.guild.default_role, read_messages=True, send_messages=False)
        await self.announcements.set_permissions(self.player_role, read_messages=True, send_messages=False)
        await self.register_channel.set_permissions(self.player_role, send_messages=True, read_messages=True)
        await self.submissions.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False)
        await self.submissions.set_permissions(self.player_role, read_messages=False, send_messages=False)

    @commands.command()
    async def register(self, ctx):
        player = ctx.message.author
        guild = ctx.guild

        if self.player_count < self.limit and self.game_started and ctx.channel.id == self.register_channel.id:
            await player.add_roles(self.player_role)
            self.players.append(player)
            self.player_count += 1

            submissions_channel = await guild.create_text_channel(player.name + "-submissions", category=self.submissions)
            await submissions_channel.set_permissions(player, read_messages=True, send_messages=True) 
            await ctx.send(ctx.message.author.mention + ", you have been registered!")
        elif not self.game_started:
            await ctx.send("The game hasn't even started yet!")
        elif ctx.channel.id != self.register_channel.id:
            await ctx.send("You cannot register here.")
        else:
            await ctx.send("Registration has ended. Try again next time!")

        if self.player_count < self.limit:
            await ctx.send("**Registration has ended. Try again next time!**")
            await self.register_channel.set_permissions(self.player_role, send_messages=False)

    @commands.command()
    async def create_rooms(self, ctx, room_count, room_capacity):
        room_count = int(room_count)
        room_capacity = int(room_capacity)

        self.room_capacity = room_capacity

        if self.game_started and room_capacity * room_count >= self.player_count:
            guild = ctx.guild

            for i in range(room_count):
                room_role = await guild.create_role(name="Room " + str(i + 1))
                room = await guild.create_text_channel("room-" + str(i + 1), category=self.category) 
                await room.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False, read_message_history=False)
                await room.set_permissions(room_role, read_messages=True, send_messages=True, read_message_history=False)
                self.room_roles[room] = room_role
                self.role_rooms[room_role] = room
                self.player_room_roles[room_role] = []
                self.rooms[room] = 0


            indexes = [i for i in range(self.player_count)]

            while indexes != []:
                
                room_selection = random.choice(list(self.rooms.keys()))

                if self.rooms[room_selection] > room_capacity:
                    continue

                self.rooms[room_selection] += 1

                player_selection = self.players[indexes.pop(random.randrange(len(indexes)))]
                await player_selection.add_roles(self.room_roles[room_selection])

                self.player_room_roles[self.room_roles[room_selection]].append(player_selection)

            self.rooms_created = True
        elif room_capacity * room_count < self.player_count:
            await ctx.send("You cannot create rooms with those constraints.")
        else:
            await ctx.send("No game in progress.")


    @commands.command()
    async def move(self, ctx, room_number):

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

                elif self.rooms[dest_room] >= self.room_capacity:
                    await ctx.send("This room is at room limit! Use ```-status``` to find an empty room.")
                else:
                    await ctx.send("Rooms have not been created yet.")
                
                return

        await ctx.send("Room not found. Ensure that you typed in a room that exists using the ```-status``` command.")


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
        
    @commands.command()
    async def delete_all(self, ctx):
        for room in self.rooms.keys():
            await room.delete()

        for role in self.room_roles.values():
            await role.delete()

        await self.player_role.delete()

        await self.register_channel.delete()

        await self.announcements.delete()

        await self.category.delete()

    @commands.command()
    async def end_rooms(self, ctx):
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

    @commands.command()
    async def start_timer(self, ctx, time_input):
        try:
            try:
                time = int(time_input)
            except:
                convertTimeList = {'s':1, 'm':60, 'h':3600, 'd':86400, 'S':1, 'M':60, 'H':3600, 'D':86400}
                time = int(time_input[:-1]) * convertTimeList[time_input[-1]]
            if time > 86400:
                await ctx.send("Please enter a value less than 24 hours.")
                return
            if time <= 0:
                await ctx.send("Please enter a non-negative value.")
                return
            if time >= 3600:
                message = await self.announcements.send(f"Timer: {time//3600}:{time%3600//60}:{time%60}")
            elif time >= 60:
                message = await self.announcements.send(f"Timer: {time//60}:{time%60}")
            elif time < 60:
                message = await self.announcements.send(f"Timer: {time}")
            while True:
                try:
                    await asyncio.sleep(1)
                    time -= 1
                    if time >= 3600:
                        await message.edit(content=f"Timer: {time//3600}:{time %3600//60}:{time%60}")
                    elif time >= 60:
                        await message.edit(content=f"Timer: {time//60}:{time%60}")
                    elif time < 60:
                        await message.edit(content=f"Timer: {time}")
                    if time <= 0:
                        await message.edit(content=f"Timer: {time}")
                        await self.announcements.send(f"{self.player_role.mention}s, the countdown has ended! Rooms are now closing.")
                        await asyncio.sleep(10)
                        await self.end_rooms(ctx)
                        break
                except:
                    break
        except:
            await ctx.send(f"Alright, first you gotta let me know how I\'m gonna time **{time_input}**....")

    @commands.command()
    async def vote(self, ctx, name):
        pass

    

def setup(client):
	client.add_cog(Xquester(client))



    
