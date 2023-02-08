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
        self.coins = data["coins"]
        self.prestige = data["prestige"]
        self.totalpeople = data["totalpeople"]
        self.discovered = data["discovered"]
        self.population = [person(p["serial"], p["parents"], genes=p["genes"]) for p in data["population"]]
        self.lastegg = get(data["lastegg"], tzinfo="Asia/Singapore")
        self.hatchery = [egg(p["serial"], p["parents"], get(p["hatchtime"], tzinfo="Asia/Singapore"), genes=p["genes"], mutation=p["mutation"]) for p in data["hatchery"]] 

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
        await interaction.response.defer()
        if interaction.user.id == self.id:
            data = imdata(id=self.id)
            collected = 0 
            ncoins = 0
            collectembed = discord.Embed(title="collection complete!")
            newg = [] 

            for new in data["hatchery"]:
                if arrow.Arrow.now() > get(new["hatchtime"]):
                    data["population"].append(person(new["serial"], new["parents"], genes=new["genes"]))
                    collectembed.add_field(name=f':baby: person {new["serial"]} ({new["genes"]})', value=f'**mutations: {new["mutation"]}**\nparents: {", ".join([str(x) for x in new["parents"]])}')
                    collected += 1
                    ncoins += sum([26-value(g) for g in new["genes"]])
                    if new["genes"] not in data["discovered"]:
                        data["discovered"].append(new["genes"])
                        newg.append(new["genes"])

            collectembed.description = f"you collected {collected} eggs and got {ncoins} coins.\n" + ("new combos: " + ", ".join(newg) if len(newg) != 0 else "no new combos found.")
            data["totalpeople"] += collected
            initlevel = data["level"]
            while (data["level"] + 1) * (data["level"] + 2) / 2 <= len(data["discovered"]):
                data["level"] += 1
            data["hatchery"] = [egg for egg in data["hatchery"] if get(egg["hatchtime"]) >= arrow.Arrow.now()]
            data["lastegg"] = max([get(egg["hatchtime"]) for egg in data["hatchery"]] + [arrow.Arrow.now()])
            data["coins"] += ncoins
            await interaction.followup.send(embed=collectembed, ephemeral=True)
            exdata(data, id=self.id)
            if data["level"] != initlevel:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="level up!",
                        description=f"you've leveled up to level {data['level']}!"
                    ), 
                    ephemeral=True
                )

            nextegg = data["lastegg"] + timedelta(seconds=5*data["level"])

            while len(data["hatchery"]) < data["level"] + 1:
                parents = sample(data["population"], 2)
                genes = newgenes(*[p["genes"] for p in parents])
                data["hatchery"].append(egg(data["totalpeople"]+len(data["hatchery"])+1, list(sorted([p["serial"] for p in parents])), nextegg, genes=genes[0], mutation=genes[1]))
                nextegg += timedelta(seconds=5*data["level"])

            exdata(data, id=self.id)

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
                ndata[x] = [{"serial": p.serial, "parents": p.parents, "hatchtime": p.hatchtime, "genes": p.genes, "mutation": p.mutation} if isinstance(p, egg) else p for p in ndata[x]]
    if id:
        data[str(id)] = ndata
    else:
        data = ndata
    json.dump(data, open("data.json", "w"), default=str, indent=4)

def value(genes):
    return sum([alpha.index(x) for x in genes])

def evolchance(gene):
    return alpha.index(gene) / 100 

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

def embedlen(embed): #copied from stackoverflow
    # embed would be the discord.Embed instance
    fields = [embed.title, embed.description, embed.footer.text, embed.author.name]

    fields.extend([field.name for field in embed.fields])
    fields.extend([field.value for field in embed.fields])

    total = ""
    for item in fields:
        # If we str(discord.Embed.Empty) we get 'Embed.Empty', when
        # we just want an empty string...
        total += str(item) if str(item) != 'Embed.Empty' else ''

    return len(total)

# constants
alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
firstgenes = newgenes("ZZ", "ZZ")
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
            "genes": firstgenes[0],
            "mutation": firstgenes[1]
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
    await interaction.response.defer()

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

    await interaction.followup.send("how to use `/run`:", embeds=embeds)

@bot.tree.command(name="population", description="see your population")
async def population(interaction, bottomfirst: Optional[bool], sort_by_serial: Optional[bool], full: Optional[bool] = False):
    await interaction.response.defer()

    print(f"/population was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    population = user(interaction.user.id).population
    population = list(sorted(population, key=lambda x: x.serial if sort_by_serial else value(x.genes)))
    if bottomfirst:
        population = list(reversed(population))

    people = [population[25*x:min(25*(x+1), len(population))] for x in range(math.ceil(len(population)/25))]
    embeds = []
    for x in range(len(people)):
        embeds.append(discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s population :people_holding_hands:", description=f"page {x+1} of {len(people)}"))
        for p in people[x]:
            embeds[-1].add_field(name=f"person {p.serial} ({p.genes})", value=f"parents: {p.parents[0]}, {p.parents[1]}")
    
    if not full:
        embeds = [embeds[0]]

    await interaction.followup.send(embeds=embeds)

@bot.tree.command(name="hatchery", description="hatchery")
async def hatchery(interaction):
    global egg
    await interaction.response.defer()

    print(f"/hatchery was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    hatchery = user(interaction.user.id).hatchery
    population = user(interaction.user.id).population
    totalpeople = user(interaction.user.id).totalpeople

    limit = user(interaction.user.id).level

    nextegg = user(interaction.user.id).lastegg + timedelta(seconds=5*limit)

    while len(hatchery) < limit + 1:
        parents = sample(population, 2)
        genes = newgenes(*[p.genes for p in parents])
        hatchery.append(egg(totalpeople+len(hatchery)+1, list(sorted([p.serial for p in parents])), nextegg, genes=genes[0], mutation=genes[1]))
        nextegg += timedelta(seconds=5*limit)

    nextegg = arrow.Arrow.now()

    while True:
        await asyncio.sleep(1)

        embed = discord.Embed(
            title=f"{interaction.user.display_name} ({interaction.user.name})'s hatchery :egg:", 
            description=f"{limit+1} eggs"
        )

        for x in range(limit+1):
            try:
                e = hatchery[x]
                embed.add_field(
                    name=f"slot {x+1}" + (" :hatching_chick:" if e.hatchtime < arrow.Arrow.now() else " :egg:"), 
                    value=f"**person {e.serial}\nmutations: {e.mutation}**\nparents: {e.parents[0]}, {e.parents[1]}\nhatching {format_timestamp(e.hatchtime, TimestampType.RELATIVE)}"
                )
            except:
                pass

        try:
            await msg.edit(embed=embed, view=hatcheryview(interaction.user.id))
        except:
            try:
                msg
            except:
                msg = await interaction.followup.send(embed=embed, view=hatcheryview(interaction.user.id))
            else:
                break
        data = imdata(interaction.user.id)
        data["hatchery"] = hatchery
        exdata(data, id=interaction.user.id)

@bot.tree.command(name="fuckery", description="fuckery")
async def fuckery(interaction, person1: str, person2: str, times: str):
    await interaction.response.defer()

    print(f"/fuckery was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    data = imdata(id=interaction.user.id)
    parents = [person1, person2] 
    try:
        parents = [int(parents[x]) if parents[x] != "max" else sorted(data["population"], key=lambda p: value(p["genes"]))[x]["serial"] for x in range(2)]
        parents = [[x for x in data["population"] if x["serial"] == p][0] for p in parents]
    except:
        await interaction.followup.send(embed=error_embed("serial numbers"))
        return
    ncoins = 0
    newg = []
    children = []
    embeds = [discord.Embed(title="fuckery complete! :hot_face:")]

    if times == "max":
        atimes = math.floor(data["coins"]/(25*data["level"]))
    else:
        try:
            atimes = min(math.floor(data["coins"]/(25*data["level"])), int(times))
        except:
            await interaction.followup.send(embed=error_embed("times"))
            return

    data["coins"] -= atimes * 25 * data["level"]

    atimes = min(atimes, 250)

    for x in range(atimes):
        genes = newgenes(*[p["genes"] for p in parents])
        new = egg(data["totalpeople"]+len(data["hatchery"])+x+1, list(sorted([p["serial"] for p in parents])), arrow.Arrow.now(), genes=genes[0], mutation=genes[1])
        data["population"].append(person(new.serial, new.parents, genes=new.genes))
        children.append(new)
        ncoins += sum([26-value(g) for g in new.genes])
        if new.genes not in data["discovered"]:
            data["discovered"].append(new.genes)
            newg.append(new.genes)

    embeds.append(discord.Embed(title=f"offspring", description=f"page {1} of {math.ceil(len(children)/25)}"))
    for x in range(len(children)):
        new = children[x] 
        nname = f':baby: person {new.serial} {new.genes}'
        ndesc = f'\n**mutations: {new.mutation}**'
        if sum(embedlen(embed) for embed in embeds) + len(nname) + len(ndesc) >= 6000:
            break
        else:
            if len(embeds[-1].fields) == 25 or embedlen(embeds[-1]) + len(nname) + len(ndesc) >= 6000:
                embeds.append(discord.Embed(title=f"offspring", description=f"page {len(embeds)+1} of {math.ceil(len(children)/25)}")) 
            embeds[-1].add_field(name=nname, value=ndesc)

    embeds[0].description = f"you collected {atimes} eggs and got {ncoins} coins.\n" + ("new combos: " + ", ".join(newg) if len(newg) != 0 else "no new combos found.")
    data["totalpeople"] += atimes 
    initlevel = data["level"]
    while (data["level"] + 1) * (data["level"] + 2) / 2 <= len(data["discovered"]):
        data["level"] += 1
    data["hatchery"] = [egg for egg in data["hatchery"] if get(egg["hatchtime"]) >= arrow.Arrow.now()]
    data["lastegg"] = arrow.Arrow.now()
    data["coins"] += ncoins

    await interaction.followup.send(embeds=embeds[:min(10, len(embeds))])
    exdata(data, id=interaction.user.id)
    if data["level"] != initlevel:
        await interaction.followup.send(embed=discord.Embed(
            title="level up!",
            description=f"you've leveled up to level {data['level']}!"
        ))

@bot.tree.command(name="selection", description="selection")
async def selection(interaction, gene: str):
    await interaction.response.defer()

    print(f"/selection was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    try:
        alpha.index(gene)
    except:
        await interaction.followup.send(embed=error_embed("genes"))
        return

    data = imdata(id=interaction.user.id)
    
    discovered = min(alpha.index(x) for y in data["discovered"] for x in y) 

    try:
        if gene == "max":
            remove = discovered+5
        else:
            remove = max(discovered+5, alpha.index(gene))
    except:
        await interaction.followup.send("ha you thought")
    else:
        sizes = {p: len(data[p]) for p in ["population", "hatchery"]}
        for p in ["population", "hatchery"]:
            ndata = []
            for person in data[p]:
                rmable = [alpha.index(x) >= remove for x in person["genes"]]
                if rmable.count(True) != len(rmable):
                    ndata.append(person)
            data[p] = ndata
        coins = sum(sizes[x] - len(data[x]) for x in sizes)
        await interaction.followup.send(embed=discord.Embed(
            title = f"(un)natural selection :skull: (both genes {alpha[remove]} and below)",
            description = f"you got {coins} coins.\n" + "\n".join([f"{x}: {sizes[x]} :arrow_right: {len(data[x])}" for x in sizes])
        ))
        data["coins"] += coins
        exdata(data, id=interaction.user.id)

@bot.tree.command(name="viewprofile", description="view your profile")
async def profile(interaction):
    await interaction.response.defer()

    print(f"/viewprofile was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")
    
    data = imdata(id=interaction.user.id)

    bio = data["profile"]["bio"]

    if bio == "":
        bio = "you have not picked a bio. use `/editprofile` to add a bio to your account."

    image = data["profile"]["image"]

    embed = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s profile", description=f"{bio}") 
   
    embed.set_thumbnail(url=interaction.user.avatar)
    embed.set_image(url=image)

    for x in ["level", "coins", "total people"]:
        embed.add_field(name=x, value=data["".join([y for y in x if y != " "])])

    embed.add_field(name="population", value=len(data["population"]))
    embed.add_field(name="discovered", value=len(data["discovered"]))
    embed.add_field(name="highest discovered", value=sorted(data["discovered"], key=lambda x: (value(x), min(value(y) for y in x)))[0])

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="editprofile", description="update your gif/bio in your profile.")
async def editprof(interaction, updating: str, newvalue: str):
    await interaction.response.defer()

    print(f"/editprofile was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    data = imdata(id=interaction.user.id)    
    
    if updating in ["bio", "image"]:
        data["profile"][updating] = newvalue
        exdata(data, id=interaction.user.id)
        embed = discord.Embed(title=f"your new {updating}!", description=(f"your {updating} has been set to ```{newvalue}```" if updating == "bio" else f"your {updating} has been updated!") + "\ncheck `/viewprofile` to see how it looks!")
    else:
        await interaction.followup.send(embed=error_embed("variable"))
        return

    await interaction.followup.send(embed=embed)

    exdata(data, id=interaction.user.id)

bot.run(TOKEN)
