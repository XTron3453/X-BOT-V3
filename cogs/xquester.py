from atexit import register
from click import command
from discord.ext import commands
import discord
import random

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
        self.announcements = None
        self.register_channel = None
        self.rooms_created = False
        self.rooms = {}
        self.room_roles = {}
        self.player_room_roles = {}

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
            await ctx.send(ctx.message.author.mention + ", you have been registered!")
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

        self.room_capacity = room_capacity

        if self.game_started and room_capacity * room_count >= self.player_count:
            guild = ctx.guild

            for i in range(room_count):
                room_role = await guild.create_role(name="Room " + str(i + 1))
                room = await guild.create_text_channel("room-" + str(i + 1), category=self.category) 
                await room.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False, read_message_history=False)
                await room.set_permissions(room_role, read_messages=True, send_messages=True, read_message_history=False)
                self.room_roles[room] = room_role
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

        print(self.player_room_roles[self.room_roles[ctx.channel]])
        print(len(self.player_room_roles[self.room_roles[ctx.channel]]))


        if self.rooms_created and len(self.player_room_roles[self.room_roles[ctx.channel]]) < self.room_capacity:

            new_role = None

            for role in self.room_roles.values():
                if role.name == "Room " + int(room_number):
                    await ctx.message.author.remove_roles(self.room_roles[ctx.channel])
                    await ctx.message.author.add_roles(role)
                    break
            
            await ctx.send("Room not found. Ensure that you typed in a room that exists using the ```-status``` command.")

        elif len(self.player_room_roles[ctx.channel]) >= self.room_capacity:
            ctx.send("This room is at room limit! Use ```-status``` to find an empty room.")
        else:
            ctx.send("Rooms have not been created yet.")


    @commands.command()
    async def status(self, ctx):
        if self.rooms_created:
            message = ""

            print(self.player_room_roles)
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

        self.player_role.delete()

def setup(client):
	client.add_cog(Xquester(client))



    
