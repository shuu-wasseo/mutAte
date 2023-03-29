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
        self.totalvessels = data["totalvessels"]
        self.discovered = data["discovered"]
        self.registered = data["registered"]
        self.population = [
            vessel(
                p["serial"], p["parents"], genes=p["genes"]
            ) for p in data["population"]
        ] 
        self.lastegg = get(data["lastegg"])
        self.hatchery = [
            egg(
                p["serial"], p["parents"], get(p["hatchtime"]), 
                genes=p["genes"], mutation=p["mutation"]
            ) for p in data["hatchery"]
        ] 
        self.cemetery = [
            vessel(p["serial"], p["parents"], genes=p["genes"]) 
            for p in data["cemetery"]
        ] 
        self.upgrades = data["upgrades"]

class vessel:
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
        self.procreatechance = value(self.genes[1])
 
class egg(vessel):
    def __init__(self, serial, parents, hatchtime, genes = "", mutation = 0):
        super().__init__(serial, parents, genes)
        self.hatchtime = hatchtime
        self.mutation = mutation

class fighter:
    def __init__(self, genes):
        self.genes = genes
        stats = [value(x) for x in genes]
        self.attack = max(1, randint(stats[0]-1, stats[0]+1))
        self.health = max(1, randint(stats[1]-1, stats[1]+1))

# embeds
class error_embed(discord.Embed):
    def __init__(self, err, need=0):
        super().__init__()
        self.title = f"error! invalid {err}."
        if err == "coins":
            self.description = f"you need {int(need)} coins per egg."
        elif err == "lowgenes":
            self.title = "error. your genes are not rare enough."
            self.description = f"you need to have one vessel with a gene of rarity U or higher to do selection."
        elif err == "highgenes":
            self.title = "error. your genes are too rare."
            self.description = f"you haven't gone far enough in the game to select these genes!"
        elif err == "max upgrade":
            self.title = f"error. {err}."
            self.description = f"you have bough the maximum amount of this upgrade (4)."
        else:
            server = "https://discord.gg/CZs6CkZZfd"
            self.description = f"check `/help` to see if your {err} is in the right format." 
            self.description += f"otherwise, please join the support server here.\n{server}" 
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
            cembed = discord.Embed(title="collection complete!")
            newg = [] 
            discovered = min(alpha.index(x) for y in data["discovered"] for x in y)

            for new in data["hatchery"]:
                if arrow.Arrow.now() > get(new["hatchtime"]):
                    data["population"].append(vessel(
                        new["serial"], new["parents"], 
                        genes=new["genes"], birthtime=arrow.Arrow.now()
                    )) 
                    cembed.add_field(
                        name=f':baby: vessel {new["serial"]} ({emojify(new["genes"])})', 
                        value=f'**mutations: {new["mutation"]}**\n' 
                        + f'parents: {", ".join([str(x) for x in new["parents"]])}' 
                    ) 
                    collected += 1
                    ncoins += sum(value(g) for g in new["genes"])
                    if new["genes"] not in data["discovered"]:
                        data["discovered"].append(new["genes"])
                        newg.append(new["genes"])

            cembed.description = f"you collected {collected} eggs and got {ncoins} coins.\n" 
            if len(newg) != 0: 
                cembed.description += "new combos: " + ", ".join(newg) 
            else:
                cembed.description += "no new combos found." 
            data["totalvessels"] += collected
            initlevel = data["level"]
            while (data["level"] + 1) * (data["level"] + 2) / 2 <= len(data["discovered"]):
                data["level"] += 1
            data["hatchery"] = [
                egg for egg in data["hatchery"] 
                if get(egg["hatchtime"]) >= arrow.Arrow.now()
            ] 
            data["lastegg"] = max(
                [get(egg["hatchtime"]) for egg in data["hatchery"]] 
                + [arrow.Arrow.now()]
            ) 
            data["currency"]["coins"] += ncoins
            await interaction.followup.send(embed=cembed, ephemeral=True)
            exdata(data, id=self.id)
            if data["level"] != initlevel:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="level up!",
                        description=f"you've leveled up to level {data['level']}!"
                    ), 
                    ephemeral=True
                )

            interval = 5*data["level"]*(100-data["upgrades"]["hwt5-"]*5)/100
            nextegg = data["lastegg"]
            nextegg += timedelta(seconds=interval) 

            while len(data["hatchery"]) < data["level"] + 1:
                parents = parentsample(data["population"])
                genes = newgenes(
                    *[p["genes"] for p in parents], 
                    upgrade=data["upgrades"]["mc5+"]
                ) 
                data["hatchery"].append(egg(
                    data["registered"]+1, list(sorted([p["serial"] for p in parents])), nextegg, 
                    genes=genes[0], mutation=genes[1]
                )) 
                nextegg += timedelta(seconds=interval) 
                data["registered"] += 1

            exdata(data, id=self.id)

            ndiscovered = min(alpha.index(x) for y in data["discovered"] for x in y)
            if ndiscovered < discovered:
                await interaction.followup.send(
                    embed=unlock(alpha[ndiscovered]), 
                    ephemeral=True
                ) 

# views
class upgradeview(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id
        self.data = imdata(id=id)

    async def upgrade(self, interaction, upg):
        if interaction.user.id == self.id:
            data = imdata(id=interaction.user.id)
            if data["currency"]["researchpoints"] >= 5 ** data["upgrades"][upg] and not (upg == "sl1-" and data["upgrades"][upg] >= 4):
                data["currency"]["researchpoints"] -= 5 ** data["upgrades"][upg]
                data["upgrades"][upg] += 1
                exdata(data, id=interaction.user.id)
                embed = discord.Embed(
                    title="upgrade!", 
                    description=f"you have upgraded {upg} to {upg[-1]}{data['upgrades'][upg]*5}%!"
                )
            elif (upg == "sl1-" and data["upgrades"][upg] >= 4):
                embed = error_embed("max upgrade")
            else:
                price = 5 ** data['upgrades'][upg]
                embed = discord.Embed(
                    title="not enough research points :skull:", 
                    description=f"you need {price} research points to buy this. get more and try again!" 
                ) 
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

    @discord.ui.button(label="rp1+",style=discord.ButtonStyle.green)
    async def rp1(self, interaction, button):
        await self.upgrade(interaction, "rp1+")
        pass

    @discord.ui.button(label="sl1-",style=discord.ButtonStyle.green)
    async def sl1(self, interaction, button):
        await self.upgrade(interaction, "sl1-")
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
            embed.add_field(name="number of dormant vessels", value=len(cemetery))
            embed.add_field(name="average genes", value=''.join(avg))
            await interaction.response.send_message(embed=embed)

            cemetery = [fighter(x["genes"]) for x in cemetery]
            enemies = sample(cemetery, len(cemetery))
            data = {"cemetery": cemetery, "enemies": enemies}
            exdata(data, id=self.id, game=True)

            gdata = imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            user = interaction.user
            embed = discord.Embed(
                title=f"{user.display_name} ({user.name})'s afterlife :skull:" 
            ) 
            battlefield = {"vessel": cemetery[0], "enemy": enemies[0]}
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                embed.add_field(
                    name=warrior, 
                    value=f"{emojify(fighterobj['genes'])}\n"
                    + f":punch: {fighterobj['attack']}\n"
                    + f":heart: {fighterobj['health']}" 
                ) 
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
                data["currency"]["researchpoints"] += value(enemies[0]["genes"])
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
            title, description = "", ""
            if [cemetery, enemies] == [[], []]:
                title = "it's a tie!"
                description = f"oh well. at least you still got research points." 
            elif cemetery == []:
                title = "you lost."
                description = f"oh well. at least you still got research points," 
            elif enemies == []:
                title = "you won!"
                description = "slay! enjoy your new research points!"
            await interaction.followup.send(embed=discord.Embed(
                title=title, description=description
            )) 
            exdata({"cemetery": [], "enemies": []}, id=self.id, game=True)
            maing["cemetery"] = []
            exdata(maing, id=self.id)
        else:
            myact, cemetery, enemies = self.turn(
                cemetery, enemies, 
                action=action
            )
            youract, enemies, cemetery = self.turn(
                enemies, cemetery, 
                action=choice(["attack", "heal"]
            )) 

            embed = discord.Embed(title=f"you {action}!", description="")
            desc = "you " + myact + "\n" + "enemy " + youract + "\n\n"
            data = {"cemetery": cemetery, "enemies": enemies}
            for x in data:
                if data[x][0]["health"] <= 0:
                    val = value(data[x][0]["genes"])
                    desc += ("you" if x == "cemetery" else "an enemy") + f" died. "
                    desc += (f"(and you got {val} research points!)" if x != "cemetery" else "") + "\n" 
                    maing["currency"]["researchpoints"] += val
                    data[x] = data[x][1:]
                    if x == "cemetery":
                        maing[x] = maing[x][1:]
            exdata(maing, id=self.id)
            exdata(data, id=self.id, game=True)
            embed.description = desc
            await interaction.followup.send(embed=embed, ephemeral=True)

            gdata = imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            user = interaction.user
            embed = discord.Embed(
                title=f"{user.display_name} ({user.name})'s afterlife :skull:"
            ) 
            try:
                battlefield = {"vessel": cemetery[0], "enemy": enemies[0]}
            except:
                title, description = "", ""
                if [cemetery, enemies] == [[], []]:
                    title = "it's a tie!"
                    description = f"oh well. at least you still got research points." 
                elif cemetery == []:
                    title = "you lost."
                    description = f"oh well. at least you still got research points," 
                elif enemies == []:
                    title = "you won!"
                    description = "slay! enjoy your new research points!"
                await interaction.followup.send(embed=discord.Embed(
                    title=title, description=description
                ))
                exdata({"cemetery": [], "enemies": []}, id=self.id, game=True)
                return
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                left = len(gdata[list(gdata.keys())[list(battlefield.keys()).index(warrior)]])
                embed.add_field(
                    name=warrior, 
                    value=f"{left} left\n{emojify(fighterobj['genes'])}\n"
                    + f":punch: {fighterobj['attack']}\n:heart: {fighterobj['health']}") 
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
        options = {
            "introduction": "welcome to the game!",
            "commands": "so how the hell do i use this bot",
            "numbers": "crunching some numbers (for the curious vessels)",
            "genes": "introducing every gene and its themes",
            "afterlife": "the research minigame"
        }

        options = [
            discord.SelectOption(label=o, description=options[o]) for o in options
        ]

        super().__init__(
            placeholder='saurr what do you need help with', 
            min_values=1, max_values=1, options=options
        ) 
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        match self.values[0]:
            case "introduction":
                help = {
                    "welcome to the game!\nthis game is about population control.": {
                        "how it\'s going": "years pass, and society is flourishing. very recently, a new biological breakthrough has allowed the discover of superhuman genes which can be used to help humanity. the potential of these genes are limitless, and scientists estimate that they are capable of infrequent mutation up to 25 times their original state, each mutation bringing forth new frontiers of research.", 
                        "how do i mutate?": "the current state of technology allows for a biological construct known as a vessel. though incapable of sentience, vessels are living organisms containing two gene traits each and can undergo evolution to mutate new genes. vessels need some time to be synthesized from eggs, however. the genes vessels contain are represented by letters A-Z, Z being the original state and A being the most advanced gene.",
                        "aim of the game": "you start off with 2 vessels with ZZ genes. your goal is to, through population control, finally have one vessel with AA genes." 
                    },
                    "how do i get someone with AA genes?\nthere are a few ways!": {
                        "reproduction": "your vessels are able to synthesize offspring in the form of new vessels. every 'baby' vessel inherits its traits from its parents, and there is a tiny chance of mutation resulting in an advancement in genes! slowly, you'll get better and better genes.", 
                        "frickery": "if needed, you are able to make your vessels manually undergo reproduction. this is especially useful if you pick out vessels with the best genes as there is a higher chance that the genes of the babies will mutate!", 
                        "selection": "the amount of babies that can be synthesized at once is very limited. to allow for a better gene pool, you may be allowed to permanently shut down vessels with weaker genes to increase the general quality of your population's genes." 
                    },
                    "but what about the dormant vessels?\ndon't worry, you'll still get to see them": {
                        "cemetery": "check out your dormant vessels! they are living a very peaceful life.",
                        "afterlife minigame": "active vessels are VERY volatile. as such, research can only be conducted on the vessels in their 'afterlife', when they are dormant. the best way to do this is to obviously watch them fight! you will be taking control of a dormant vessel and be facing against an artificial enemy which can test their skills to the maximum." 
                    },
                    "what kind of currency is there in this game?\nthere are two main types:": {
                        "coins": "earned when a new baby is synthesized\nused for **frickery**",
                        "researchpoints": "earned from research conducted when an active vessel shuts down or from the afterlife minigame\nused for **upgrades**" 
                    },
                    "what if my progression is too slow?\nyou can always buy upgrades from the upgrade shop using research points!": {}, 
                    "bonus tips\nyou'll probably need these, thank me later": {
                        "hatchery": "at once, only a limited amount of vessels can be synthesized at once. these baby vessels are the offspring of randomly selected vessels, so do carry out unnatural selection as to increase the quality of your gene pool.",
                        "lifespan": "active vessels die out automatically over time! the lifespan of your first few vessels will be generally very short, so make sure you're active especially in the first few days.", 
                        "upgrades": "these help a lot with the progression, especially in later stages when the population stops mutating so rapidly.", 
                        "afterlife": "the afterlife minigame gives you a lot of research points. do use it optimally. in addition, dormant vessels that undergo the minigame will unfortunately have to be destroyed.", 
                        "selection": "selection has a similar reward to afterlife, but it also boosts your hatchery (and thus your population) due to the better gene pool. so remember to do it regularly!" 
                    }
                }
            case "commands":
                help = {
                    "the main game\nsee your population and watch it expand": {
                        "population": "view population (default: top 25 vessels in gene quality).\n\n`bottomfirst`: view reverse ranking\n`sort_by_serial`: rank by (low) serial instead\n`full`: see up to 250 vessels", 
                        "hatchery": "view your hatchery (shows all your eggs).\n\n`level + 1` slots in total\ngain 1 egg every `5 * level` minutes (without upgrades)" 
                    },
                    "population control\nreally really really unnatural wae": {
                        "frickery": "force two vessels to instantly synthesize as many babies as you want (and can), for 5 * level coins per baby.\n\n`vessel1`, `vessel2`: the serial numbers of the two vessels who you would like to reproduce (or `max` to get the vessels with the best genes)\n`times`: number of times you would like the vessels to reproduce (or `max` for the maximum number of times)", 
                        "selection": "shut down all active vessels where both genes are a certain tier or below. only all vessels with both genes 5 tiers below your highest discovered gene or lower (e.g. discovering U unlocks selection for vessels with both slots Z and below)\nyou will get one research point per vessel killed.\n\n`gene`: all vessels with both genes with this tier or below will be killed." 
                    },
                    "the dormant vessels\nbecause we're not done with them yet!": {
                        "cemetery": "just `/population` but for the dormant vessels.",
                        "afterlife": "starts the afterlife minigame."
                    },
                    "misc\nupgrades and profiles!": {
                        "help": "this command!",
                        "upgrade": "view and buy upgrades! the currency used here is research points.",
                        "me": "view your profile and some stats.",
                        "editprofile": "edit your image or bio,\n\n`updating`: the thing you want to update (image or bio)\n`newvalue`: the new url / bio" 
                    }
                }
            case "numbers":
                help = {
                    "the numbers!\nif you were curious.": {
                        "base chance of mutation (%)": "25 for Z, 0 for A\n(-1 per tier)",
                        "base hatching time (min)\nfrickery price (coins)": "5 * level",
                        "value of vessel's genes": "1 for Z, 26 for A for each gene\n(+1 per tier)",
                        "lifespan (12 hours)\npower (afterlife)": "value of left gene",
                        "likelihood of procreation\nhealth (afterlife)": "value of right gene"
                    }
                }
            case "afterlife":
                help = {
                    "afterlife\nresearching the dormant vessels!": {
                        "what kind of game is this?": "afterlife is somewhat a turn-based game. in each turn, the user and enemy can choose to either attack or heal.", 
                        "you vs. the enemy": "you will be playing as a 'queue' of dormant vessels who still have a bit of life left in them to fight. the opponent is a randomly generated 'queue' of combat vessels based on your own dormant population.", 
                        "attacking and healing": "each player can either attack (for attack stat ± 1) or heal (for enemy attack stat / 2 ± 1). the attack and initial health stat for each player is based on their left and right genes respectively.", 
                        "clearing the queue": "when one vessel 'dies' in any 'queue', we move on to the next vessel as the previous vessel is now destroyed and will not be seen again. oh well, at least they spent their last moments fruitfully.", 
                        "winning the game": "whoever has their queue clear first wins. if both queues become clear at the same time, it's a tie.", 
                        "researchpoints": "you also get research points for every enemy vessel you kill! this is based on the value of their genes (see the numbers section for more info)." 
                    }
                }
            case "genes":
                help = {
                    "the genes\nthere are a total of 26 (for now), each with its own unique theme.": {
                        f"tier {5-x}": "\n".join(f'{emojify(y)}: {genes[y]["theme"]}' for y in alpha[x*5:x*5+5]) for x in range(5) 
                    }
                } 
                help[list(help.keys())[0]]["tier 0"] = f"{emojify('A')}: {genes['A']['theme']}"
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
    for x in range(5):
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

def exdata(ndata, id=None, game=False):
    file = "game.json" if game else "data.json"
    data = json.load(open(file, "r"))
    if id:
        for x in ndata:
            if x in objects.keys():
                if x in ["cemetery", "enemies"] and game:
                    ndata[x] = [[vars(p) if isinstance(p, objects[x]) else p for p in l] for l in ndata[x]]
                else:
                    ndata[x] = [vars(p) if isinstance(p, objects[x]) else p for p in ndata[x]]
                    if x == ["hatchery"]:
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
    if alpha.index(gene) >= 5:
        kill = emojify(alpha[max(alpha.index(gene)-5, 0)])
        desc = f"you now can run `/selection`"
        if gene != "U":
            desc += " again " 
        else:
            desc += " "
        desc += f"and kill off all vessels with {kill} or below for both genes." 
    else:
        desc = "keep grinding!"
    
    return discord.Embed(
        title=f"you've unlocked {emojify(gene)}!", 
        description=desc 
    )
def autodie(id):
    data = imdata(id)
    try:
        data["population"]
    except:
        print(data)
    else:
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
        prochance = []
        for p in pop:
            try:
                procreatechance = p.procreatechance
            except:
                procreatechance = p["procreatechance"]
            try:
                prochance.append(prochance[-1] + procreatechance)
            except:
                prochance.append(procreatechance)
        prochance = [x/prochance[-1] for x in prochance]
        choose = random()
        for x in range(len(prochance)):
            if choose < prochance[x]:
                parents.append(pop[x])
                break
    return parents

async def sendhelp(interaction, help):
    embeds = []

    for x, y in help.items():
        embeds.append(discord.Embed(
            title = x.split("\n")[0],
            description = x.split("\n")[1]
        )) 
        for c, h in y.items():
            embeds[-1].add_field(name = c, value = h, inline = True)

    await interaction.followup.send(embeds=embeds, view=helpview())

def emojify(gs):
    return "".join([
        f"<:gene{x}:{genes[x]['emoji']}>" 
        if 'emoji' in genes[x] else x 
        for x in gs
    ]) 
	

def log(com, int):
    print(f"/{com} was used in {int.channel} ({int.guild}) by {int.user}.")

# constants
alpha = "ZYXWVUTSRQPONMLKJIHGFEDCBA"
firstgenes = newgenes("ZZ", "ZZ")

upgs = {
    "mc5+": ["increase mutation chance by 5%", "mutation chance increased by"],
    "hwt5-": ["reduce hatchery waiting time for each egg by 5%", "hatchery waiting time for each egg reduced by"], 
    "fp5-": ["reduce frickery price by 5%", "frickery price reduced by"],
    "rp1+": ["increase research points per vessel by 1", "research points per vessel increased by"],
    "sl1-": ["reduce selection limit by 1 (min 1)", "selection limit reduced by"]
}

initdata = {
    "level": 1,
    "currency": {
        "coins": 4,
        "researchpoints": 0
    },
    "prestige": 0,
    "totalvessels": 2,
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
            "procreatechance": 1
        },
        {
            "serial": 2,
            "parents": [0, 0],
            "genes": "ZZ",
            "birthtime": arrow.Arrow.now(),
            "lifespan": timedelta(hours=12),
            "deathtime": arrow.Arrow.now() + timedelta(hours=12),
            "procreatechance": 1
        }
    ],
    "lastegg": arrow.Arrow.now(),
    "hatchery": [],
    "cemetery": [],
    "upgrades": {u: 0 for u in upgs.keys()},
    "profile": {
        "bio": "",
        "image": ""
    }
}

objects = {
    "population": vessel,
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
    'Q': {
        'theme': 'wind',
        'emoji': '1078502812335476756'
    }, 
    'P': {
        'theme': 'thunder',
        'emoji': '1078713565063688192'
    }, 
    'O': {
        'theme': 'blood',
        'emoji': '1085827501646938192'
    }, 
    'N': {
        'theme': 'poison',
        'emoji': '1080125177343508560'
    }, 
    'M': {
        'theme': 'acid',
        'emoji': '1080747911140343828'
    },
    'L': {
        'theme': 'amber',
        'emoji': '1081899477025173524'
    }, 
    'K': {
        'theme': 'steel',
        'emoji': '1082264329052749864'
    }, 
    'J': {
        'theme': 'gold',
        'emoji': '1083344132061274122'
    }, 
    'I': {
        'theme': 'flame',
        'emoji': '1084325043435225158'
    }, 
    'H': {
        'theme': 'magma',
        'emoji': '1085827255906873364'
    }, 
    'G': {
        'theme': 'crystals',
        'emoji': '1085873444559790110'
    }, 
    'F': {'theme': 'light'}, 
    'E': {'theme': 'abyss'}, 
    'D': {'theme': 'plasma'}, 
    'C': {'theme': 'gravity'}, 
    'B': {'theme': 'singularity'}, 
    'A': {'theme': 'stars'}
}
gamemsg = {}
