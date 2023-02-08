# bot.py

# mini checklist for me
# - something to do with the people you killed off

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
from datetime import timedelta, datetime 
from arrow import arrow, get
from discord_timestamps import format_timestamp, TimestampType

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for guild in self.guilds:
            self.tree.clear_commands(guild=guild)
        #self.tree.add_command(self.tree.get_command("help"), override=True)
        await self.tree.sync()

bot = MyClient(intents=intents)

topg = os.getenv('TOPGG_TOKEN')

# game classes
class user:
    def __init__(self, id):
        data = imdata(id=id)
        self.level = data["level"]
        self.prestige = data["prestige"]
        self.totalpeople = data["totalpeople"]
        self.population = [person(p["serial"], p["parents"], genes=p["genes"]) for p in data["population"]]
        self.lastegg = get(data["lastegg"], tzinfo="Asia/Singapore")
        self.hatchery = [egg(p["serial"], p["parents"], get(p["hatchtime"], tzinfo="Asia/Singapore"), genes=p["genes"]) for p in data["hatchery"]] 

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

class egg(person):
    def __init__(self, serial, parents, hatchtime, genes = "", mutation = 0):
        super().__init__(serial, parents, genes)
        self.hatchtime = hatchtime
        self.mutation = mutation

# embeds
class error_embed(discord.Embed):
    def __init__(self, error):
        super().__init__()
        self.title = f"error! invalid {error}."
        self.description = f"check `/help` to see if your {error.split()[-1]} is in the right format. otherwise, please join the support server here.\nhttps://discord.gg/GPfpUNmxPP"
        self.color = discord.Color.dark_red()

# views
class hatcheryview(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id

    @discord.ui.button(label="collect all",style=discord.ButtonStyle.green)
    async def collectall(self, interaction, button):
        if interaction.user.id == self.id:
            data = imdata(id=self.id)
            collected = 0 
            ncoins = 0
            collectembed = discord.Embed(title="collection complete!")
            new = [] 

            for egg in data["hatchery"]:
                if arrow.Arrow.now() > get(egg["hatchtime"]):
                    data["population"].append(person(egg["serial"], egg["parents"], genes=egg["genes"]))
                    collectembed.add_field(name=f'person {egg["serial"]} {egg["genes"]}', value=f'parents: {", ".join([str(x) for x in egg["parents"]])}')
                    collected += 1
                    ncoins += sum([26-value(g) for g in egg["genes"]])
                    if egg["genes"] not in data["discovered"]:
                        data["discovered"].append(egg["genes"])
                        new.append(egg["genes"])

            collectembed.description = f"you collected {collected} eggs and got {ncoins} coins.\n" + ("new combos:" + str(new)[1:-1] if len(new) != 0 else "no new combos found.")
            data["totalpeople"] += collected
            initlevel = data["level"]
            while (data["level"] + 1) * (data["level"] + 2) / 2 <= len(data["discovered"]):
                data["level"] += 1
            data["hatchery"] = [egg for egg in data["hatchery"] if get(egg["hatchtime"]) >= arrow.Arrow.now()]
            data["lastegg"] = arrow.Arrow.now()
            data["coins"] += ncoins
            await interaction.response.send_message(embed=collectembed)
            exdata(data, id=self.id)
            if data["level"] != initlevel:
                await interaction.followup.send(embed=discord.Embed(
                    title="level up!",
                    description=f"you've leveled up to level {data['level']}!"
                ))

# mini methods
def imdata(id=None):
    data = json.load(open("data.json", "r"))
    if id:
        try:
            return data[str(id)]
        except:
            data = initdata
            exdata(data, id=id)
            return data 
    return data

def exdata(ndata, id=None):
    data = json.load(open("data.json", "r"))
    if id:
        for x in ndata:
            if x == "population":
                ndata[x] = [{"serial": p.serial, "parents": p.parents, "genes": p.genes} if isinstance(p, person) else p for p in ndata[x]]
            elif x == "hatchery":
                ndata[x] = [{"serial": p.serial, "parents": p.parents, "hatchtime": p.hatchtime, "genes": p.genes} if isinstance(p, egg) else p for p in ndata[x]]
    if id:
        data[str(id)] = ndata
    else:
        data = ndata
    json.dump(data, open("data.json", "w"), default=str, indent=4)

def value(genes):
    return sum([alpha.index(x) for x in genes])

def evolchance(gene):
    return 0.1 * (0.1 ** ((25 - value(gene)) / 25)) 

def newgenes(gene1, gene2):
    genes = ""
    mutation = []
    for x in range(2):
        chance = random()
        if chance < 0.5:
            inherit = gene1[x] 
        else:
            chance -= 0.5
            inherit = gene2[x]
        if chance < evolchance(inherit)/2:
            genes += alpha[max(alpha.index(inherit.upper())-1, 0)]
        else:
            genes += inherit
        mutation.append(chance < evolchance(inherit)/2)
    return genes, mutation.count(True)

# constants
alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
initdata = {
    "level": 1,
    "coins": 4,
    "prestige": 0,
    "totalpeople": 2,
    "discovered": ["ZZ"],
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
    "lastegg": arrow.Arrow.now(),
    "hatchery": [
        {
            "serial": 3,
            "parents": [1, 2],
            "hatchtime": arrow.Arrow.now(),
            "genes": newgenes("ZZ", "ZZ")[0]
        }
    ],
    "profile": {
        "bio": "",
        "image": ""
    }
}

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
async def population(interaction, bottomfirst: Optional[bool], sort_by_serial: Optional[bool]):
    print(f"/population was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    population = user(interaction.user.id).population
    population = list(sorted(population, key=lambda x: x.serial if sort_by_serial else value(x.genes)))
    if bottomfirst:
        population = list(reversed(population))

    people = [population[25*x:min(25*(x+1), len(population))] for x in range(math.ceil(len(population)/25))]
    embeds = []
    for x in range(len(people)):
        embeds.append(discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s population", description=f"page {x+1} of {len(people)}"))
        for p in people[x]:
            embeds[-1].add_field(name=f"person {p.serial} ({p.genes})", value=f"parents: {p.parents[0]}, {p.parents[1]}")

    await interaction.response.send_message(embeds=embeds)

@bot.tree.command(name="hatchery", description="hatchery")
async def hatchery(interaction):
    global egg

    print(f"/hatchery was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    hatchery = user(interaction.user.id).hatchery
    population = user(interaction.user.id).population

    limit = user(interaction.user.id).level

    nextegg = user(interaction.user.id).lastegg + timedelta(seconds=10*limit)

    while len(hatchery) < limit + 1:
        parents = sample(population, 2)
        genes = newgenes(*[p.genes for p in parents])
        hatchery.append(egg(len(population)+len(hatchery)+1, list(sorted([p.serial for p in parents])), nextegg, genes=genes[0], mutation=genes[1]))
        nextegg += timedelta(seconds=10*limit)

    nextegg = arrow.Arrow.now()

    embed = discord.Embed(
        title=f"{interaction.user.display_name} ({interaction.user.name})'s population", 
        description=f"{limit+1} eggs"
    )

    for x in range(limit+1):
        try:
            e = hatchery[x]
            embed.add_field(
                name=f"slot {x+1}" + " (HATCHED)" if e.hatchtime < arrow.Arrow.now() else "", 
                value=f"**person {e.serial}\n{e.mutation} mutations**\nparents: {e.parents[0]}, {e.parents[1]}\nhatching {format_timestamp(e.hatchtime, TimestampType.RELATIVE)}"
            )
        except:
            pass

    await interaction.response.send_message(embed=embed, view=hatcheryview(interaction.user.id))

    data = imdata(interaction.user.id)
    data["hatchery"] = hatchery
    exdata(data, id=interaction.user.id)

@bot.tree.command(name="viewprofile", description="view your profile")
async def profile(interaction):
    print(f"/viewprofile was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")
    
    data = imdata(id=interaction.user.id)

    bio = data["profile"]["bio"]

    if bio == "":
        bio = "you have not picked a bio. use `/editprofile` to add a bio to your account."

    image = data["profile"]["image"]

    embed = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s profile", description=f"{bio}") 
   
    embed.set_thumbnail(url=interaction.user.avatar)
    embed.set_image(url=image)

    for x in ["level", "total people"]:
        embed.add_field(name=x, value=data["".join([y for y in x if y != " "])])

    embed.add_field(name="population", value=len(data["population"]))
    embed.add_field(name="discovered", value=len(data["discovered"]))
    embed.add_field(name="highest discovered", value=sorted(data["discovered"], key=lambda x: value(x))[0])

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="editprofile", description="update your gif/bio in your profile.")
async def editprof(interaction, updating: str, newvalue: str):
    print(f"/editprofile was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    data = imdata(id=interaction.user.id)    
    
    if updating in ["bio", "image"]:
        data["profile"][updating] = newvalue
        exdata(data, id=interaction.user.id)
        embed = discord.Embed(title=f"your new {updating}!", description=(f"your {updating} has been set to ```{newvalue}```" if updating == "bio" else f"your {updating} has been updated!") + "\ncheck `/viewprofile` to see how it looks!")
    else:
        embed = discord.Embed(title="invalid variable!", description="please use either 'bio' or 'image'.")

    await interaction.response.send_message(embed=embed)

    exdata(data, id=interaction.user.id)

bot.run(TOKEN)
