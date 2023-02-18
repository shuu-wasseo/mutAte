import mini
import discord
from arrow import get, arrow
from datetime import timedelta
from random import random, choice, sample, randint

class user:
    def __init__(self, id):
        data = mini.imdata(id=id)
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
                    best = min([mini.alpha.index(p.genes[x]) for p in parents])
                    self.genes += mini.alpha[max(0, best-1)]
        self.birthtime = birthtime
        self.lifespan = timedelta(hours=(26-mini.value(self.genes[0]))*12)
        self.deathtime = birthtime + self.lifespan
        self.charisma = (25-mini.value(self.genes[1]))
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
        stats = [27 - mini.value(x) for x in genes]
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
            data = mini.imdata(id=self.id)
            collected = 0 
            ncoins = 0
            collectembed = discord.Embed(title="collection complete!")
            newg = [] 
            discovered = min(mini.alpha.index(x) for y in data["discovered"] for x in y)

            for new in data["hatchery"]:
                if arrow.Arrow.now() > get(new["hatchtime"]):
                    data["population"].append(person(new["serial"], new["parents"], genes=new["genes"], birthtime=arrow.Arrow.now()))
                    collectembed.add_field(name=f':baby: person {new["serial"]} ({new["genes"]})', value=f'**mutations: {new["mutation"]}**\nparents: {", ".join([str(x) for x in new["parents"]])}')
                    collected += 1
                    ncoins += sum([26-mini.value(g) for g in new["genes"]])
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
            mini.exdata(data, id=self.id)
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
                parents = mini.parentsample(data["population"])
                genes = mini.newgenes(*[p["genes"] for p in parents], upgrade=data["upgrades"]["mc5+"])
                data["hatchery"].append(egg(data["registered"]+1, list(sorted([p["serial"] for p in parents])), nextegg, genes=genes[0], mutation=genes[1]))
                nextegg += timedelta(seconds=5*data["level"]*(100-data["upgrades"]["hwt5-"]*5)/100)
                data["registered"] += 1

            mini.exdata(data, id=self.id)

            ndiscovered = min(mini.alpha.index(x) for y in data["discovered"] for x in y)
            if ndiscovered < discovered:
                await interaction.followup.send(embed=mini.unlock(mini.alpha[ndiscovered]), ephemeral=True)

# views
class upgradeview(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id

    async def upgrade(self, interaction, upg):
        if interaction.user.id == self.id:
            data = mini.imdata(id=interaction.user.id)
            if data["currency"]["skullpoints"] >= 5 ** data["upgrades"][upg]:
                data["currency"]["skullpoints"] -= 5 ** data["upgrades"][upg]
                data["upgrades"][upg] += 1
                mini.exdata(data, id=interaction.user.id)
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
            data = mini.imdata(interaction.user.id)
            cemetery = data["cemetery"]
            skullpoints = data["currency"]["skullpoints"]
            avg = [[mini.value(x["genes"][y]) for x in cemetery] for y in range(2)]
            avg = [mini.alpha[int(sum(x)/len(x))] for x in avg]

            embed = discord.Embed(title="what's after life?")
            embed.add_field(name="number of dead people", value=len(cemetery))
            embed.add_field(name="average genes", value=''.join(avg))
            await interaction.response.send_message(embed=embed)

            cemetery = [fighter(x["genes"]) for x in cemetery]
            enemies = sample(cemetery, len(cemetery))
            data = {"cemetery": cemetery, "enemies": enemies}
            mini.exdata(data, id=self.id, game=True)

            gdata = mini.imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            embed = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s afterlife :skull:")
            battlefield = {"corpse": cemetery[0], "enemy": enemies[0]}
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                embed.add_field(name=warrior, value=f"{fighterobj['genes']}\n:punch: {fighterobj['attack']}\n:heart: {fighterobj['health']}")
            gdata = {"cemetery": cemetery, "enemies": enemies}
            mini.exdata(gdata, id=self.id, game=True) 

           

