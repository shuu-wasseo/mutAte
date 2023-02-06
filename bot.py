# bot.py

# load discord
import os
import discord
from discord import app_commands
from typing import Optional
from dotenv import load_dotenv
from random import random, randint, choice, sample
import math
import json
import asyncio
import requests
from datetime import timedelta
from arrow import arrow
from discord_timestamps import format_timestamp, TimestampType

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for guild in self.guilds:
            self.tree.clear_commands(guild=guild)
        self.tree.add_command(self.tree.get_command("help"), override=True)
        self.tree.add_command(self.tree.get_command("run"), override=True)
        await self.tree.sync()

bot = MyClient(intents=intents)

topg = os.getenv('TOPGG_TOKEN')

class user:
    def __init__(self, id):
        data = imdata(id=id)
        try:
            self.level = data["level"]
            self.prestige = data["prestige"]
            self.totalpeople = data["totalpeople"]
            self.population = [person(*p[:2], genes=p[2]) for p in data["population"]]
            self.hatchery = [person(*p[:2], genes=p[2]) for p in data["hatchery"]]
        except:
            data = {
                "level": 0,
                "prestige": 0,
                "totalpeople": 0,
                "population": [
                    {
                        "serial": 1,
                        "parents": [0, 0],
                        "genes": "ZZ"
                    },
                    {
                        "serial": 2,
                        "parents": [0, 0],
                        "genes": "ZZ"
                    }
                ],
                "hatchery": []
            }
            exdata(data, id=id)
            self.level = data["level"]
            self.prestige = data["prestige"]
            self.totalpeople = data["totalpeople"]
            self.population = [person(*p[:2], genes=p[2]) for p in data["population"]]
            self.hatchery = [person(*p[:2], genes=p[2]) for p in data["hatchery"]]

class person:
    def __init__(self, serial, parents, genes = ""):
        self.serial = serial
        self.parents = parents
        self.genes = genes
        if genes == "":
            for x in range(2):
                chance = random()
                if chance >= 0.01:
                    self.genes += choice([p.genes[x] for p in parents])
                else:
                    best = min([alpha.index(p.genes[x]) for p in parents])
                    self.genes += alpha[max(0, best-1)]
    def p(self):
        try:
            return f"person {self.serial}: genes {self.genes} (parents {self.parents[0].serial}, {self.parents[1].serial})"
        except:
            return f"person {self.serial}: genes {self.genes} (first gen)"

# embeds
class error_embed(discord.Embed):
    def __init__(self, error):
        super().__init__()
        self.title = f"error! invalid {error}."
        self.description = f"check `/help` to see if your {error.split()[-1]} is in the right format. otherwise, please join the support server here.\nhttps://discord.gg/GPfpUNmxPP"
        self.color = discord.Color.dark_red()

def imdata(id=None):
    data = json.load(open("data.json", "r"))
    if id:
        return data[str(id)]
    return data

def exdata(ndata, id=None):
    data = json.load(open("data.json", "r"))
    if id:
        data[str(id)] = ndata
    else:
        data = ndata
    json.dump(data, open("data.json", "w"), default=str)

def value(genes):
    return sum([alpha.index(x) for x in genes])

alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# the command
@bot.tree.command(name="help", description="help")
async def help(interaction):
    print(f"/help was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    help = """
so there was supposed to be a help message here but i kind of dont know what i'll be doing yet 
    """

    embed1 = discord.Embed(title = "commands", description = "these parameters must be passed.")
    for x in help.split("\n\n"):
        embed1.add_field(name = x.split("\n")[0], value = x.split("\n")[1], inline = True)

    embeds = [embed1]

    for e in embeds:
        e.color = discord.Color.teal()

    await interaction.response.send_message("how to use `/run`:", embeds=embeds)

@bot.tree.command(name="population", description="see your population")
async def population(interaction, reverse=Optional[bool], sort_by_serial=Optional[bool]):
    population = user(interaction.user.id).population
    population = list(sorted(population, key=lambda x: x.serial if sort_by_serial else value(x.genes)))
    
    people = [population[0:min(25*x, len(population))] for x in range(math.ceil(len(population)/25))]
    embeds = []
    for x in range(len(people)):
        embeds.append(discord.Embed(title="population", description=f"page {x+1} of {len(people)}"))
        for p in people[x]:
            embeds[-1].add_field(name=f"person {p.serial} ({p.genes})", value=f"parents:\n{p.parents[0]}\n{p.parents[1]}")

    await interaction.response.send_message(embeds=embeds)
