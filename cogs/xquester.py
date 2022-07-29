from atexit import register
from discord.ext import commands
import discord
import random

class Xquester(commands.Cog):
    def __init__(self, client, name='Xquester Cog'):
        self.game_started = False
        self.client = client
        self.votes = {}
        self.player_count = 0
        self.players = {}
        self.limit = -1
        self.player_role = None
        self.category = None
        self.announcements = None
        self.register_channel = None
        self.rooms = []
        self.room_roles = []

    @commands.command()
    async def create_game(self, ctx, limit):
        guild = ctx.guild

        self.game_started = True

        self.limit = int(limit)
        self.player_role = await guild.create_role(name="Player")

        self.category = await guild.create_category("Xquester")
        self.announcements = await guild.create_text_channel("announcements", category=self.category)
        self.register_channel = await guild.create_text_channel("register", category=self.category)

        await self.announcements.set_permissions(ctx.guild.default_role, read_messages=True, send_messages=False)
        await self.announcements.set_permissions(self.player_role, read_messages=True, send_messages=False)
        await self.register_channel.set_permissions(self.player_role, send_messages=True, read_messages=True)

    @commands.command()
    async def register(self, ctx):
        player = ctx.message.author

        if self.player_count < self.limit and self.game_started and ctx.channel.id == self.register_channel.id:
            await player.add_roles(self.player_role)
            self.players.append(player)
            self.player_count += 1
        elif not self.game_started:
            await ctx.send("The game hasn't even started yet!")
        elif ctx.channel.id != self.register_channel.id:
            await ctx.send("You cannot register here.")
        else:
            await self.register_channel.set_permissions(self.player_role, send_messages=False)
            await ctx.send("Registration has ended. Try again next time!")

    @commands.command()
    async def create_rooms(self, ctx, room_count, room_capacity):
        room_count = int(room_count)
        room_capacity = int(room_capacity)
        if self.game_started and room_capacity * room_count < len(self.player_count):
            guild = ctx.guild

            for i in range(int(room_count)):
                room_role = await guild.create_role(name="Room " + str(room_count + 1))
                room = await guild.create_text_channel("room-" + str(room_count + 1), category=self.category) 
                await room.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False, read_message_history=False)
                await room.set_permissions(ctx.guild.room_role, read_messages=True, send_messages=True, read_message_history=False)
                self.room_roles.append(room_role)
                self.rooms.append(room)

            indexes = [i for i in range(self.player_count)]
            room_index = 0

            while indexes != []:
                if room_index >= int(room_capacity):
                    room_index = 0

                player_selection = indexes.pop(random.randrange(len(indexes)))
                room_selection = self.rooms[room_index]
                self.players[player_selection].add_roles(self.room_roles[room_selection])

                room_index += 1
            

        

    @commands.command()
    async def move(self, ctx, room_number):
        pass

    




        

def setup(client):
	client.add_cog(Xquester(client))



    
