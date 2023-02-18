import json
import time
import discord
from arrow import arrow, get
from datetime import timedelta
from random import random, choice, sample, randint

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
            avg = [[value(x["genes"][y]) for x in cemetery] for y in range(2)]
            avg = [alpha[int(sum(x)/len(x))] for x in avg]

            embed = discord.Embed(title="what's after life?")
            embed.add_field(name="number of dead people", value=len(cemetery))
            embed.add_field(name="average genes", value=''.join(avg))
            await interaction.response.send_message(embed=embed)

            cemetery = [fighter(x["genes"]) for x in cemetery]
            enemies = sample(cemetery, len(cemetery))
            data = {"cemetery": cemetery, "enemies": enemies}
            exdata(data, id=self.id, game=True)

            gdata = imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            embed = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s afterlife :skull:")
            battlefield = {"corpse": cemetery[0], "enemy": enemies[0]}
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                embed.add_field(name=warrior, value=f"{fighterobj['genes']}\n:punch: {fighterobj['attack']}\n:heart: {fighterobj['health']}")
            gdata = {"cemetery": cemetery, "enemies": enemies}
            exdata(gdata, id=self.id, game=True) 

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
