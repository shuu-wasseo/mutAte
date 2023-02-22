import json, time, discord
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
        self.lifespan = timedelta(hours=value(self.genes[0])*12)
        self.deathtime = birthtime + self.lifespan
        self.charisma = value(self.genes[1])
 
class egg(person):
    def __init__(self, serial, parents, hatchtime, genes = "", mutation = 0):
        super().__init__(serial, parents, genes)
        self.hatchtime = hatchtime
        self.mutation = mutation

class fighter:
    def __init__(self, genes):
        self.genes = genes
        stats = [value(x) for x in genes]
        self.attack = randint(stats[0]-1, stats[0]+1)
        self.health = randint(stats[1]-1, stats[1]+1)

# embeds
class error_embed(discord.Embed):
    def __init__(self, error, need=0):
        super().__init__()
        self.title = f"error! invalid {error}."
        if error == "coins":
            self.description = f"you need {int(need)} coins per egg."
        else:
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
                    collectembed.add_field(name=f':baby: person {new["serial"]} ({emojify(new["genes"])})', value=f'**mutations: {new["mutation"]}**\nparents: {", ".join([str(x) for x in new["parents"]])}')
                    collected += 1
                    ncoins += sum(value(g) for g in new["genes"])
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
                embed.add_field(name=warrior, value=f"{emojify(fighterobj['genes'])}\n:punch: {fighterobj['attack']}\n:heart: {fighterobj['health']}")
            gdata = {"cemetery": cemetery, "enemies": enemies}
            exdata(gdata, id=self.id, game=True)
            await interaction.followup.send(embed=embed, view=afterlifeview(self.id))

class afterlifeview(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id

    def turn(self, cemetery, enemies, action = ""): 
        myact = ""
        data = imdata(id=self.id)
        num = 0
        if action == "attack":
            attack = cemetery[0]["attack"]
            num = randint(attack-1, attack+1)
            enemies[0]["health"] -= num
            if enemies[0]["health"] <= 0:
                data["currency"]["skullpoints"] += value(enemies[0]["genes"])
        elif action == "heal":
            healing = int(enemies[0]["attack"] / 2)
            num = randint(healing-1, healing+1)
            cemetery[0]["health"] += num
        myact = f"{action}(s) for {num} :heart:"
        exdata(data, id=self.id, game=True)
        return myact, cemetery, enemies

    async def action(self, action, interaction):
        await interaction.response.defer()
        data = imdata(id=self.id, game=True)
        maing = imdata(id=self.id)
        cemetery, enemies = data["cemetery"], data["enemies"]
    
        if [] in [cemetery, enemies]:
            if [cemetery, enemies] == [[], []]:
                await interaction.followup.send(embed=discord.Embed(title="it's a tie!", description=f"oh well. at least you still got skullpoints."))
            elif cemetery == []:
                await interaction.followup.send(embed=discord.Embed(title="you lost.", description=f"oh well. at least you still got skullpoints,"))
            elif enemies == []:
                await interaction.followup.send(embed=discord.Embed(title="you won!", description=f"slay!"))
            exdata({"cemetery": [], "enemies": []}, id=self.id, game=True)
            maing["cemetery"] = []
            exdata(maing, id=self.id)
        else:
            myact, cemetery, enemies = self.turn(cemetery, enemies, action=action)
            youract, enemies, cemetery = self.turn(enemies, cemetery, action=choice(["attack", "heal"]))

            embed = discord.Embed(title=f"you {action}!", description="")
            desc = "you " + myact + "\n" + "enemy " + youract + "\n\n"
            data = {"cemetery": cemetery, "enemies": enemies}
            for x in data:
                if data[x][0]["health"] <= 0:
                    val = value(data[x][0]["genes"])
                    desc += ("you" if x == "cemetery" else "an enemy") + f" died. " + (f"(and you got {val} skullpoints!)" if x != "cemetery" else "") + "\n"
                    maing["currency"]["skullpoints"] += val
                    data[x] = data[x][1:]
                    if x == "cemetery":
                        maing[x] = maing[x][1:]
            exdata(maing, id=self.id)
            exdata(data, id=self.id, game=True)
            embed.description = desc
            await interaction.followup.send(embed=embed, ephemeral=True)

            gdata = imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            embed = discord.Embed(title=f"{interaction.user.display_name} ({interaction.user.name})'s afterlife :skull:")
            try:
                battlefield = {"corpse": cemetery[0], "enemy": enemies[0]}
            except:
                if [cemetery, enemies] == [[], []]:
                    await interaction.followup.send(embed=discord.Embed(title="it's a tie!", description=f"oh well. at least you still got skullpoints."))
                elif cemetery == []:
                    await interaction.followup.send(embed=discord.Embed(title="you lost.", description=f"oh well. at least you still got skullpoints,"))
                elif enemies == []:
                    await interaction.followup.send(embed=discord.Embed(title="you won!", description=f"slay!"))
                exdata({"cemetery": [], "enemies": []}, id=self.id, game=True)
                return
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                embed.add_field(name=warrior, value=f"{len(gdata[list(gdata.keys())[list(battlefield.keys()).index(warrior)]])} left\n{emojify(fighterobj['genes'])}\n:punch: {fighterobj['attack']}\n:heart: {fighterobj['health']}")
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

class helpdropdown(discord.ui.Select):
    def __init__(self, msg = None):

        # Set the options that will be presented inside the dropdown
        options = [
            discord.SelectOption(label="introduction", description="welcome to the game!"),
            discord.SelectOption(label="commands", description="so how the hell do i use this bot"),
            discord.SelectOption(label="numbers", description="crunching some numbers (for the curious people)"),
            discord.SelectOption(label="genes", description="introducing every gene and its themes"),
            discord.SelectOption(label="afterlife", description="the dead people minigame")
        ]

        super().__init__(placeholder='saurr what do you need help with', min_values=1, max_values=1, options=options)
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        match self.values[0]:
            case "introduction":
                help = {
                    "welcome to the game!\nthis game is about population control.": {
                        "some background": "recently, scientists have found two people with special genes, and these genes have superhuman potential. as of today, these genes have been found to mutate up to 25 times beyond their original state. these 25 mutations will be referred to using the letters Y to A.",
                        "aim of the game": "you start off with 2 people with ZZ genes. your goal is to, through population control, finally have one person with AA genes."
                    },
                    "how do i get someone with AA genes?\nthere are a few ways!": {
                        "reproduction": "your people are able to produce offspring! with every offspring, there is a tiny chance of each gene mutating! slowly, you'll get better and better genes.",
                        "frickery": "if needed, you might be able to make two people procreate multiple babies! this is especially useful if you pick out people with the best genes as there is a higher chance that the genes of the babies will mutate!",
                        "selection": "to allow a better gene pool, you may be allowed to kill off people with weaker genes to increase the general quality of your population's genes."
                    },
                    "but what about the dead people?\ndon't worry, you'll still get to see them": {
                        "cemetery": "you can visit the cemetery to see how everyone is doing!",
                        "afterlife minigame": "there's a little minigame involving the dead people as a quick send-off! :>"
                    },
                    "what kind of currency is there in this game?\nthere are two main types:": {
                        "coins": "earned when a new baby is born\nused for **frickery**",
                        "skullpoints": "earned when someone dies / in the afterlife minigame\nused for **upgrades**"
                    },
                    "what if my progression is too slow?\nyou can always buy upgrades from the upgrade shop using skullpoints!": {},
                    "bonus tips\nyou'll probably need these, thank me later": {
                        "lifespan": "the lifespan of your first few people will be generally very short, so make sure you're active especially in the first few days!",
                        "upgrades": "these help a lot with the progression, especially in later stages when the population stops mutating so rapidly.",
                        "afterlife": "the afterlife minigame gives you a lot of skullpoints and helps with the progression too.",
                        "selection": "selection has a similar reward to afterlife, but it also boosts your hatchery (and thus your population) due to the better gene pool. so remember to do it regularly!"
                    }
                }
            case "commands":
                help = {
                    "the main game\nsee your population and watch it expand": {
                        "population": "view population (default: top 25 people in gene quality).\n\n`bottomfirst`: view reverse ranking\n`sort_by_serial`: rank by (low) serial instead\n`full`: see up to 250 people",
                        "hatchery": "view your hatchery (shows all your eggs).\n\n`level + 1` slots in total\ngain 1 egg every `5 * level` minutes (without upgrades)"
                    },
                    "population control\nreally really really unnatural wae": {
                        "frickery": "force two people to instantly procreate as many babies as you want (and can), for 5 * level coins per baby.\n\n`person1`, `person2`: the serial numbers of the two people who you would like to reproduce (or `max` to get the people with the best genes)\n`times`: number of times you would like the people to reproduce (or `max` for the maximum number of times)",
                        "selection": "purge all people where both genes are a certain tier or below. only all people with both genes 5 tiers below your highest discovered gene or lower (e.g. discovering U unlocks selection for people with both slots Z and below)\nyou will get one skullpoint per person killed.\n\n`gene`: all people with both genes with this tier or below will be killed."
                    },
                    "the dead people\nbecause we're not done with them yet!": {
                        "cemetery": "just `/population` but for the dead people.",
                        "afterlife": "starts the afterlife minigame."
                    },
                    "misc\nupgrades and profiles!": {
                        "help": "this command!",
                        "upgrade": "view and buy upgrades! the currency used here is skullpoints.",
                        "me": "view your profile and some stats.",
                        "editprofile": "edit your image or bio,\n\n`updating`: the thing you want to update (image or bio)\n'newvalue': the new url / bio"
                    }
                }
            case "numbers":
                help = {
                    "the numbers!\nif you were curious.": {
                        "base chance of mutation (%)": "25 for Z, 0 for A\n(-1 per tier)",
                        "base hatching time (min)\nfrickery price (coins)": "5 * level",
                        "value of person's genes": "1 for Z, 26 for A for each gene\n(+1 per tier)",
                        "lifespan (12 hours)\npower (afterlife)": "value of left gene",
                        "charisma\nhealth (afterlife)": "value of right gene"
                    }
                }
            case "afterlife":
                help = {
                    "afterlife\nsending off the dead people!": {
                        "what kind of game is this?": "afterlife is somewhat a turn-based game. in each turn, the user and enemy can choose to either attack or heal.",
                        "you vs. the enemy": "you will be playing as a 'queue' of corpses who still have a bit of life left in them to fight. the opponent is a randomly generated 'queue' of similar corpses based on your own dead population.",
                        "attacking and healing": "each player can either attack (for attack stat ± 1) or heal (for enemy attack stat / 2 ± 1). the attack and initial health stat for each player is based on their left and right genes respectively.",
                        "clearing the queue": "when one corpse 'dies' in any 'queue', we move on to the next corpse as the previous corpse is now permanently dead (if from your side) and will not be seen again. oh well, at least they lived their last days fruitfully.",
                        "winning the game": "whoever has their queue clear first wins. if both queues become clear at the same time, it's a tie.",
                        "skullpoints": "you also get skullpoints for every enemy corpse you kill! this is based on the value of their genes (see the numbers section for more info)."
                    }
                }
            case "genes":
                help = {
                    "the genes\nthere are a total of 26 (for now), each with its own unique theme.": {},
                }
                for x in range(5):
                    lgs = list(genes.keys())
                    help[f"tier {5-x}\n{emojify(lgs[x*5])} to {emojify(lgs[x*5+4])}"] = {emojify(x): genes[x]["theme"] for x in lgs[x*5:x*5+5]}
                help[f"tier 0\n{emojify('A')}"] = {emojify("A"): genes["A"]["theme"]} 
            case _:
                help = {}
        await sendhelp(interaction, help)


class helpview(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(helpdropdown())

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
    return sum(alpha.index(x)+1 for x in genes)

def evolchance(gene):
    return (26-value(gene)) / 100 

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
            genes += alpha[min(alpha.index(inherit)+1, 25)]
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
    return discord.Embed(title=f"you've unlocked {emojify(gene)}!", description=(f"you now can run `/selection`" + (" again " if gene != "U" else " ") + f"and kill off everyone with {emojify(alpha[max(alpha.index(gene)-5, 0)])} or below for both genes.") if alpha.index(gene) >= 5 and alpha.index(gene) <= 20 else "keep grinding!")

def autodie(id):
    data = imdata(id)
    for x in data["population"]:
        if get(x["deathtime"]) <= arrow.Arrow.now():
            data["cemetery"].append(x)
            data["population"].remove(x)
    exdata(data, id=id) 

def parentsample(pop):
    if pop == []:
        pop = initdata["population"]
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

async def sendhelp(interaction, help):
    embeds = []

    for x, y in help.items():
        embeds.append(discord.Embed(title = x.split("\n")[0], description = x.split("\n")[1]))
        for c, h in y.items():
            embeds[-1].add_field(name = c, value = h, inline = True)

    await interaction.followup.send(embeds=embeds, view=helpview())

def emojify(gs):
    return "".join([f"<:gene{x}:{genes[x]['emoji']}>" if 'emoji' in genes[x] else x for x in gs]) 

# constants
alpha = "ZYXWVUTSRQPONMLKJIHGFEDCBA"
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
genes = {
    'Z': {
        'theme': 'ashes', 
        'emoji': '1076353633353994280'
    }, 
    'Y': {
        'theme': 'roots', 
        'emoji': '1076353715910488125'
    }, 
    'X': {
        'theme': 'growth', 
        'emoji': '1076353790741065728'
    }, 
    'W': {
        'theme': 'cinders', 
        'emoji': '1076354182698766398'
    }, 
    'V': {
        'theme': 'blossoms', 
        'emoji': '1076354238176841808'
    }, 
    'U': {
        'theme': 'crags', 
        'emoji': '1076354317562433538'
    }, 
    'T': {
        'theme': 'sand', 
        'emoji': '1076354500727677028'
    }, 
    'S': {
        'theme': 'tide', 
        'emoji': '1076354578490085388'
    }, 
    'R': {
        'theme': 'frost', 
        'emoji': '1076354618667323443'
    }, 
    'Q': {'theme': 'wind'}, 
    'P': {'theme': 'thunder'}, 
    'O': {'theme': 'blood'}, 
    'N': {'theme': 'poison'}, 
    'M': {'theme': 'acid'},
    'L': {'theme': 'amber'}, 
    'K': {'theme': 'steel'}, 
    'J': {'theme': 'gold'}, 
    'I': {'theme': 'flame'}, 
    'H': {'theme': 'magma'},
    'G': {'theme': 'crystals'}, 
    'F': {'theme': 'colours'}, 
    'E': {'theme': 'light'}, 
    'D': {'theme': 'plasma'}, 
    'C': {'theme': 'gravity'}, 
    'B': {'theme': 'singularity'}, 
    'A': {'theme': 'stars'}
}
gamemsg = {}

