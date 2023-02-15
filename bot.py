# bot.py

# load discord
import os
import discord
from discord import app_commands
from typing import Optional
from dotenv import load_dotenv
from random import random, choice, randint, sample
import time
import math
import json
from datetime import timedelta 
from arrow import arrow, get
from discord_timestamps import format_timestamp, TimestampType

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True

load_dotenv()
TOKEN = ""
TOKEN = os.getenv('DISCORD_TOKEN')

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for guild in self.guilds:
            self.tree.clear_commands(guild=guild)
        #self.tree.add_command(self.tree.get_command("me"), override=True)
        await self.tree.sync()

bot = MyClient(intents=intents)

topg = os.getenv('TOPGG_TOKEN')

# game classes
class user:
    def __init__(self, id):
        data = imdata(id=id)
        self.level = data["level"]
        self.currency = data["currency"]
        self.prestige = data["prestige"]
        self.totalpeople = data["totalpeople"]
        self.discovered = data["discovered"]
        self.registered = data["registered"]
        self.population = [person(p["serial"], p["parents"], genes=p["genes"]) for p in data["population"]]
        self.lastegg = get(data["lastegg"], tzinfo="Asia/Singapore")
        self.hatchery = [egg(p["serial"], p["parents"], get(p["hatchtime"], tzinfo="Asia/Singapore"), genes=p["genes"], mutation=p["mutation"]) for p in data["hatchery"]]
        self.cemetery = [person(p["serial"], p["parents"], genes=p["genes"]) for p in data["cemetery"]]
        self.upgrades = data["upgrades"]

class person:
    def __init__(self, serial, parents, genes = "", birthtime = arrow.Arrow.now()):
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
        self.birthtime = birthtime
        self.lifespan = timedelta(hours=(26-value(self.genes[0]))*12)
        self.deathtime = birthtime + self.lifespan
        self.charisma = (25-value(self.genes[1]))
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

class fighter:
    def __init__(self, genes):
        self.genes = genes
        stats = [27 - value(x) for x in genes]
        self.attack = randint(stats[0]-1, stats[0]+1)
        self.health = randint(stats[1]-1, stats[1]+1)

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
            discovered = min(alpha.index(x) for y in data["discovered"] for x in y)

            for new in data["hatchery"]:
                if arrow.Arrow.now() > get(new["hatchtime"]):
                    data["population"].append(person(new["serial"], new["parents"], genes=new["genes"], birthtime=arrow.Arrow.now()))
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
            data["currency"]["coins"] += ncoins
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

            nextegg = data["lastegg"] + timedelta(seconds=5*data["level"]*(100-data["upgrades"]["hwt5-"]*5)/100)

            while len(data["hatchery"]) < data["level"] + 1:
                parents = parentsample(data["population"])
                genes = newgenes(*[p["genes"] for p in parents], upgrade=data["upgrades"]["mc5+"])
                data["hatchery"].append(egg(data["registered"]+1, list(sorted([p["serial"] for p in parents])), nextegg, genes=genes[0], mutation=genes[1]))
                nextegg += timedelta(seconds=5*data["level"]*(100-data["upgrades"]["hwt5-"]*5)/100)
                data["registered"] += 1

            exdata(data, id=self.id)

            ndiscovered = min(alpha.index(x) for y in data["discovered"] for x in y)
            if ndiscovered < discovered:
                await interaction.followup.send(embed=unlock(alpha[ndiscovered]), ephemeral=True)

# views
class upgradeview(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id

    async def upgrade(self, interaction, upg):
        if interaction.user.id == self.id:
            data = imdata(id=interaction.user.id)
            if data["currency"]["skullpoints"] >= 5 ** data["upgrades"][upg]:
                data["currency"]["skullpoints"] -= 5 ** data["upgrades"][upg]
                data["upgrades"][upg] += 1
                exdata(data, id=interaction.user.id)
                embed = discord.Embed(title="upgrade!", description=f"you have upgraded {upg} to {upg[-1]}{data['upgrades'][upg]*5}%!")
            else:
                embed = discord.Embed(title="not enough skullpoints :skull:", description=f"you need {5 ** data['upgrades'][upg]} skullpoints for this upgrade. get more skullpoints and try again.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="mc5+",style=discord.ButtonStyle.green)
    async def mc1(self, interaction, button):
        await self.upgrade(interaction, "mc5+")
        pass

    @discord.ui.button(label="hwt5-",style=discord.ButtonStyle.green)
    async def hwt1(self, interaction, button):
        await self.upgrade(interaction, "hwt5-")
        pass

    @discord.ui.button(label="fp5-",style=discord.ButtonStyle.green)
    async def fp1(self, interaction, button):
        await self.upgrade(interaction, "fp5-")
        pass

class afterlifestart(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id

    @discord.ui.button(label="let's begin!",style=discord.ButtonStyle.green)
    async def start(self, interaction, button):
        if interaction.user.id == self.id:
            data = imdata(interaction.user.id)
            cemetery = data["cemetery"]
            skullpoints = data["currency"]["skullpoints"]
            avg = [[value(x["genes"][y]) for x in cemetery] for y in range(2)]
            avg = [alpha[int(sum(x)/len(x))] for x in avg]

            embed = discord.Embed(title="what's after life?")
            embed.add_field(name="number of dead people", value=len(cemetery))
            embed.add_field(name="average genes", value=''.join(avg))
            await interaction.response.send_message(embed=embed)

            cemetery = [fighter(x["genes"]) for x in cemetery]
            enemies = sample(cemetery, len(cemetery))
            ppl = len(enemies)
            data = {"cemetery": cemetery, "enemies": enemies}
            exdata(data, id=self.id, game=True)

            gdata = imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            embed = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s afterlife :skull:")
            battlefield = {"corpse": cemetery[0], "enemy": enemies[0]}
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                embed.add_field(name=warrior, value=f"{fighterobj['genes']}\n:punch: {fighterobj['attack']}\n:heart: {fighterobj['health']}")
            msg = await interaction.followup.send(embed=embed, view=afterlifeview(self.id))
            gdata = {"cemetery": cemetery, "enemies": enemies}
            exdata(gdata, id=self.id, game=True) 

            newcoins = imdata(interaction.user.id)["currency"]["skullpoints"] - skullpoints
            
             
class afterlifeview(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id

    def turn(self, cemetery, enemies, action = choice(["attack", "heal"])):
        myact = ""
        data = imdata(id=self.id)
        if action == "attack":
            attack = cemetery[0]["attack"]
            num = randint(attack-1, attack+1)
            enemies[0]["health"] -= num
            myact = f":heart: -{num}"
            if enemies[0]["health"] <= 0:
                data["currency"]["skullpoints"] += 52-value(enemies[0]["genes"])
        elif action == "heal":
            healing = int(enemies[0]["attack"] / 2)
            num = randint(healing-1, healing+1)
            cemetery[0]["health"] += num
            myact = f":heart: -{num}" 
        exdata(data, id=self.id, game=True)
        return myact, cemetery, enemies

    async def action(self, action, interaction):
        data = imdata(id=self.id, game=True)
        cemetery, enemies = data["cemetery"], data["enemies"]

        # fix the final updating of values
        # skullpoints
        if [cemetery, enemies] == [[], []]:
            await interaction.followup.send(embed=discord.Embed(title="it's a tie!", description=f"oh well. at least you still got skullpoints."))
        elif cemetery == []:
            await interaction.followup.send(embed=discord.Embed(title="you lost.", description=f"oh well. at least you still got skullpoints,"))
        elif enemies == []:
            await interaction.followup.send(embed=discord.Embed(title="you won!", description=f"slay!"))
        else:
            myact, cemetery, enemies = self.turn(cemetery, enemies, action=action)
            youract, enemies, cemetery = self.turn(enemies, cemetery)

            embed = discord.Embed(title=f"you {action}!", description="")
            desc = "you " + myact + "\n" + "enemy " + youract + "\n\n"
            data = {"cemetery": cemetery, "enemies": enemies}
            for x in data:
                if data[x][0]["health"] <= 0:
                    desc += ("you" if x == "cemetery" else "an enemy") + " died.\n"
                    data[x] = data[x][1:]
            exdata(data, id=self.id, game=True)
            embed.description = desc
            await interaction.response.send_message(embed=embed, ephemeral=True)

            gdata = imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            embed = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s afterlife :skull:")
            battlefield = {"corpse": cemetery[0], "enemy": enemies[0]}
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                embed.add_field(name=warrior, value=f"{len(gdata[list(gdata.keys())[list(battlefield.keys()).index(warrior)]])}\n{fighterobj['genes']}\n:punch: {fighterobj['attack']}\n:heart: {fighterobj['health']}")
            try:
                msg = gamemsg[self.id]
                await msg.edit(embed=embed, view=afterlifeview(self.id))
            except:
                msg = await interaction.followup.send(embed=embed, view=afterlifeview(self.id))
                gamemsg[self.id] = msg
            gdata = {"cemetery": cemetery, "enemies": enemies}
            exdata(gdata, id=self.id, game=True)

    @discord.ui.button(label="attack",style=discord.ButtonStyle.green)
    async def attack(self, interaction, button):
        if interaction.user.id == self.id:
            await self.action("attack", interaction)

    @discord.ui.button(label="heal",style=discord.ButtonStyle.green)
    async def heal(self, interaction, button):
        if interaction.user.id == self.id:
            await self.action("heal", interaction)

# mini methods
def imdata(id=None, game=False):
    data = {}
    while 1:
        try:
            file = "game.json" if game else "data.json"
            data = json.load(open(file, "r"))
            if id:
                try: 
                    return data[str(id)]
                except:
                    data = initdata
                    exdata(data, id=id)
                    return data 
            return data
        except:
            time.sleep(0.1)
    return data

def exdata(ndata, id=None, game=False):
    file = "game.json" if game else "data.json"
    data = json.load(open(file, "r"))
    if id:
        for x in ndata:
            if x in objects.keys():
                ndata[x] = [vars(p) if isinstance(p, objects[x]) else p for p in ndata[x]]
                if x == "hatchery":
                    ndata[x] = sorted(ndata[x], key=lambda x:x["serial"])
            elif x == "currency":
                ndata[x] = {y: round(ndata[x][y]) for y in ndata[x]}
    if id:
        data[str(id)] = ndata
    else:
        data = ndata
    json.dump(data, open(file, "w"), default=str, indent=4)

def value(genes):
    return sum([alpha.index(x) for x in genes])

def evolchance(gene):
    return alpha.index(gene) / 100 

def newgenes(gene1, gene2, upgrade=0):
    genes = ""
    mutation = []
    for x in range(2):
        chance = random()
        if chance < 0.5:
            inherit = gene1[x] 
        else:
            chance -= 0.5
            inherit = gene2[x]
        finalchance = evolchance(inherit)/2 * (100 + upgrade*5)/100
        if chance < finalchance:
            genes += alpha[max(alpha.index(inherit.upper())-1, 0)]
        else:
            genes += inherit
        mutation.append(chance < finalchance)
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

def unlock(gene):
    return discord.Embed(title=f"you've unlocked {gene}!", description=f"you now can run `/selection` again and kill of everyone with {alpha[min(alpha.index(gene)+5, 25)]} or below for both genes.")

def autodie(id):
    data = imdata(id)
    for x in data["population"]:
        if get(x["deathtime"]) <= arrow.Arrow.now():
            data["cemetery"].append(x)
            data["population"].remove(x)
    exdata(data, id=id) 

def parentsample(pop):
    parents = []
    for x in range(2):
        charis = []
        for p in pop:
            try:
                charisma = p.charisma
            except:
                charisma = p["charisma"]
            try:
                charis.append(charis[-1] + charisma)
            except:
                charis.append(charisma)
        charis = [x/charis[-1] for x in charis]
        choose = random()
        for x in range(len(charis)):
            if choose < charis[x]:
                parents.append(pop[x])
                break
    return parents

# constants
alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
firstgenes = newgenes("ZZ", "ZZ")
initdata = {
    "level": 1,
    "currency": {
        "coins": 4,
        "skullpoints": 0
    },
    "prestige": 0,
    "totalpeople": 2,
    "discovered": ["ZZ"],
    "registered": 3,
    "population": [
        {
            "serial": 1,
            "parents": [0, 0],
            "genes": "ZZ",
            "birthtime": arrow.Arrow.now(),
            "lifespan": timedelta(hours=12),
            "deathtime": arrow.Arrow.now() + timedelta(hours=12),
            "charisma": 1
        },
        {
            "serial": 2,
            "parents": [0, 0],
            "genes": "ZZ",
            "birthtime": arrow.Arrow.now(),
            "lifespan": timedelta(hours=12),
            "deathtime": arrow.Arrow.now() + timedelta(hours=12),
            "charisma": 1
        }
    ],
    "lastegg": arrow.Arrow.now(),
    "hatchery": [],
    "cemetery": [],
    "upgrades": {
        "mc5+": 0,
        "hwt5-": 0,
        "fp5-": 0
    },
    "profile": {
        "bio": "",
        "image": ""
    }
}
upgs = {
    "mc5+": ["increase mutation chance by 5%", "mutation chance increased by"],
    "hwt5-": ["reduce hatchery waiting time for each egg by 5%", "hatchery waiting time for each egg reduced by"],
    "fp5-": ["reduce fuckery price by 5%", "fuckery price reduced by"]
}
objects = {
    "population": person,
    "hatchery": egg,
    "cemetery": fighter,
    "enemies": fighter
}
gamemsg = {}

# help command
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

# the main game
@bot.tree.command(name="population", description="see your population")
async def population(interaction, bottomfirst: Optional[bool], sort_by_serial: Optional[bool], full: Optional[bool] = False):
    autodie(interaction.user.id)

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
            embeds[-1].add_field(name=f"person {p.serial} ({p.genes})", value=f"parents: {p.parents[0]}, {p.parents[1]}\ndeath {format_timestamp(p.deathtime, TimestampType.RELATIVE)}")
    
    if not full:
        embeds = [embeds[0]]

    await interaction.followup.send(embeds=embeds)

@bot.tree.command(name="hatchery", description="hatchery")
async def hatchery(interaction):
    autodie(interaction.user.id)

    global egg
    await interaction.response.defer()

    print(f"/hatchery was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    data = user(interaction.user.id)

    hatchery = data.hatchery
    population = data.population
    registered = data.registered
    limit = data.level

    try:
        nextegg = max(get(egg.hatchtime) for egg in hatchery) + timedelta(seconds=5*limit*(100-data.upgrades["hwt5-"]*5)/100)
    except:
        nextegg = arrow.Arrow.now()

    while len(hatchery) < limit + 1:
        parents = parentsample(population)
        genes = newgenes(*[p.genes for p in parents], upgrade=data.upgrades["mc5+"])
        hatchery.append(egg(registered+1, list(sorted([p.serial for p in parents])), nextegg, genes=genes[0], mutation=genes[1]))
        nextegg += timedelta(seconds=5*limit*(100-data.upgrades["hwt5-"]*5)/100)
        registered += 1

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

    await interaction.followup.send(embed=embed, view=hatcheryview(interaction.user.id))
 
    data = imdata(interaction.user.id)
    data["hatchery"] = hatchery
    data["registered"] = registered
    exdata(data, id=interaction.user.id)

@bot.tree.command(name="fuckery", description="fuckery")
async def fuckery(interaction, person1: str, person2: str, times: str):
    autodie(interaction.user.id)

    await interaction.response.defer()

    print(f"/fuckery was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    data = imdata(id=interaction.user.id)
    discovered = min(alpha.index(x) for y in data["discovered"] for x in y)
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
    price = 5 * data["level"] * (100-data["upgrades"]["fp5-"]*5)/100

    if times == "max":
        atimes = math.floor(data["currency"]["coins"]/(5*data["level"] * (100-data["upgrades"]["fp5-"]*5)/100))
    else:
        try:
            atimes = min(math.floor(data["currency"]["coins"]/(5*data["level"])), int(times))
        except:
            await interaction.followup.send(embed=error_embed("times"))
            return

    data["currency"]["coins"] -= atimes * price

    atimes = min(atimes, 250)

    for x in range(atimes):
        genes = newgenes(*[p["genes"] for p in parents], upgrade=data["upgrades"]["mc5+"])
        new = egg(data["registered"]+1, list(sorted([p["serial"] for p in parents])), arrow.Arrow.now(), genes=genes[0], mutation=genes[1])
        data["population"].append(person(new.serial, new.parents, genes=new.genes))
        data["registered"] += 1
        children.append(new)
        ncoins += sum([26-value(g) for g in new.genes])
        if new.genes not in data["discovered"]:
            data["discovered"].append(new.genes)
            newg.append(new.genes)

    embeds.append(discord.Embed(title=f"offspring of parents {', '.join(str(p['serial']) for p in parents)}", description=f"page {1} of {math.ceil(len(children)/25)}"))
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
    data["currency"]["coins"] += ncoins

    await interaction.followup.send(embeds=embeds[:min(10, len(embeds))])
    exdata(data, id=interaction.user.id)
    if data["level"] != initlevel:
        await interaction.followup.send(embed=discord.Embed(
            title="level up!",
            description=f"you've leveled up to level {data['level']}!"
        ))

    ndiscovered = min(alpha.index(x) for y in data["discovered"] for x in y)
    if ndiscovered < discovered:
        await interaction.followup.send(embed=unlock(alpha[ndiscovered]), ephemeral=True)

@bot.tree.command(name="selection", description="selection")
async def selection(interaction, gene: str):
    autodie(interaction.user.id)

    await interaction.response.defer()

    print(f"/selection was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    try:
        alpha.index(gene)
    except:
        if gene != "max":
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
            data["cemetery"] += [x for x in data[p] if x not in ndata]
            data[p] = ndata
        skpoints = sum(sizes[x] - len(data[x]) for x in sizes)
        await interaction.followup.send(embed=discord.Embed(
            title = f"(un)natural selection :skull: (both genes {alpha[remove]} and below)",
            description = f"you got {skpoints} skullpoints.\n" + "\n".join([f"{x}: {sizes[x]} :arrow_right: {len(data[x])}" for x in sizes])
        ))
        data["currency"]["skullpoints"] += skpoints
        exdata(data, id=interaction.user.id)

        ndiscovered = min(alpha.index(x) for y in data["discovered"] for x in y)
        if ndiscovered < discovered:
            await interaction.followup.send(embed=unlock(alpha[ndiscovered]), ephemeral=True)

# dead people
@bot.tree.command(name="cemetery", description="view your cemetery")
async def cemetery(interaction, bottomfirst: Optional[bool], sort_by_serial: Optional[bool], full: Optional[bool] = False):
    autodie(interaction.user.id)

    await interaction.response.defer()

    print(f"/cemetery was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    cemetery = user(interaction.user.id).cemetery
    cemetery = list(sorted(cemetery, key=lambda x: x.serial if sort_by_serial else value(x.genes)))
    if bottomfirst:
        cemetery = list(reversed(cemetery))

    people = [cemetery[25*x:min(25*(x+1), len(cemetery))] for x in range(math.ceil(len(cemetery)/25))]
    embeds = []
    for x in range(len(people)):
        embeds.append(discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s cemetery :people_holding_hands:", description=f"page {x+1} of {len(people)}"))
        for p in people[x]:
            embeds[-1].add_field(name=f"person {p.serial} ({p.genes}) :skull:", value=f"parents: {p.parents[0]}, {p.parents[1]}")
    
    if not full:
        embeds = [embeds[0]]

    await interaction.followup.send(embeds=embeds)

@bot.tree.command(name="afterlife", description="get rid of the dead people")
async def afterlife(interaction):
    autodie(interaction.user.id)
    
    await interaction.response.defer()

    print(f"/afterlife was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    embed = discord.Embed(title="what's after life?", description="what after life nae mame strife")

    await interaction.followup.send(embed=embed, view=afterlifestart(interaction.user.id))

# upgrade commands
@bot.tree.command(name="upgrades", description="buy some upgrades")
async def upgrades(interaction):
    autodie(interaction.user.id)

    await interaction.response.defer()

    print(f"/upgrades was used in {interaction.channel} ({interaction.guild}) by {interaction.user}.")

    data = imdata(id=interaction.user.id)

    embed = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s upgrades", description=f"time to improve the game even further!\nyou have {data['currency']['skullpoints']} skullpoints.")

    for u in data["upgrades"]:
        count = data['upgrades'][u]
        embed.add_field(name=f"{u}", value=f"**{upgs[u][0]}**\ncurrently {u[-1]}{count*5}%\nnext {u[-1]}{(count+1)*5}%\ncosts {5**count} skullpoints")

    await interaction.followup.send(embed=embed, view=upgradeview(interaction.user.id))

# profile commands
@bot.tree.command(name="me", description="view your profile and stats")
async def profile(interaction):
    autodie(interaction.user.id)

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

    for x in ["level", "total people"]:
        embed.add_field(name=x, value=data["".join([y for y in x if y != " "])])

    for c in ["coins", "skullpoints"]:
        embed.add_field(name=c, value=data["currency"]["".join([y for y in c if y != " "])])
    embed.add_field(name="population", value=len(data["population"]))
    embed.add_field(name="discovered", value=len(data["discovered"]))
    embed.add_field(name="highest discovered", value=sorted(data["discovered"], key=lambda x: (value(x), min(value(y) for y in x)))[0])

    embed2 = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s numbers", description="just some little stats hehe")

    embed2.add_field(name="level-based", value="multipliers based solely on your level", inline=False)
    embed2.add_field(name="number of slots", value=data["level"]+1)
    embed2.add_field(name="base time taken for each egg (s)", value=data["level"]*5)
    embed2.add_field(name="base fuckery price", value=data["level"]*5)

    embed2.add_field(name="upgrade-based", value="multipliers based on your upgrades", inline=False)
    for u in data["upgrades"]:
        embed2.add_field(name=u, value=f"{upgs[u][1]} {data['upgrades'][u]*5}%")

    await interaction.followup.send(embeds=[embed, embed2])

@bot.tree.command(name="editprofile", description="update your gif/bio in your profile.")
async def editprof(interaction, updating: str, newvalue: str):
    autodie(interaction.user.id)

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

@bot.event
async def on_ready():
    print(f'{bot.user} is online.')
    print(f'in {len(bot.guilds)} servers')
    for x in bot.guilds:
        print(f'connected to {x.name}')
    print()
    await bot.setup_hook()

bot.run(TOKEN)
