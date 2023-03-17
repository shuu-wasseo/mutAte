# bot.py

# load discord
import os, discord, math
from discord import app_commands
from typing import Optional
from dotenv import load_dotenv
from datetime import timedelta 
from arrow import arrow, get
from discord_timestamps import format_timestamp, TimestampType

import mini

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN = "" if not TOKEN else TOKEN

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for guild in self.guilds:
            self.tree.clear_commands(guild=guild)
        await self.tree.sync()

bot = MyClient(intents=intents)

topg = os.getenv('TOPGG_TOKEN')

gamemsg = {}

# help command
@bot.tree.command(name="help", description="help")
async def help(interaction):
    await interaction.response.defer()

    mini.log("help", interaction) 

    help = {"help!\npick an option to proceed": {}}

    await mini.sendhelp(interaction, help)
    
class afterlifestart(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id

    @discord.ui.button(label="let's begin!",style=discord.ButtonStyle.green)
    async def start(self, interaction, button):
        if interaction.user.id == self.id:
            data = mini.imdata(interaction.user.id)
            cemetery = data["cemetery"]
            avg = [[mini.value(x["genes"][y]) for x in cemetery] for y in range(2)]
            avg = [mini.alpha[int(sum(x)/len(x))] for x in avg]

            embed = discord.Embed(title="what's after life?")
            embed.add_field(name="number of dormant vessels", value=len(cemetery))
            embed.add_field(name="average genes", value=''.join(avg))
            await interaction.response.send_message(embed=embed)

            cemetery = [mini.fighter(x["genes"]) for x in cemetery]
            enemies = mini.sample(cemetery, len(cemetery))
            data = {"cemetery": cemetery, "enemies": enemies}
            mini.exdata(data, id=self.id, game=True)

            gdata = mini.imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            user = interaction.user
            embed = discord.Embed(
                title=f"{user.display_name} ({user.name})'s afterlife research :skull:" 
            ) 
            battlefield = {"vessel": cemetery[0], "enemy": enemies[0]}
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                embed.add_field(
                    name=warrior, 
                    value=f"{mini.emojify(fighterobj['genes'])}\n"
                    + f":punch: {fighterobj['attack']}\n"
                    + f":heart: {fighterobj['health']}" 
                ) 
            gdata = {"cemetery": cemetery, "enemies": enemies}
            mini.exdata(gdata, id=self.id, game=True)
            await interaction.followup.send(embed=embed, view=afterlifeview(self.id))

class afterlifeview(discord.ui.View):
    def __init__(self, id):
        super().__init__()
        self.id = id

    def turn(self, cemetery, enemies, action = ""): 
        myact = ""
        data = mini.imdata(id=self.id)
        num = 0
        if action == "attack":
            attack = cemetery[0]["attack"]
            num = mini.randint(attack-1, attack+1)
            enemies[0]["health"] -= num
            if enemies[0]["health"] <= 0:
                data["currency"]["researchpoints"] += mini.value(enemies[0]["genes"]) * (data["upgrades"]["rp1+"] + 1)
        elif action == "heal":
            healing = int(enemies[0]["attack"] / 2)
            num = mini.randint(healing-1, healing+1)
            cemetery[0]["health"] += num
        myact = f"{action}(s) for {num} :heart:"
        mini.exdata(data, id=self.id, game=True)
        return myact, cemetery, enemies

    async def action(self, action, interaction):
        await interaction.response.defer()
        data = mini.imdata(id=self.id, game=True)
        maing = mini.imdata(id=self.id)
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
            mini.exdata({"cemetery": [], "enemies": []}, id=self.id, game=True)
            maing["cemetery"] = []
            mini.exdata(maing, id=self.id)
        else:
            myact, cemetery, enemies = self.turn(
                cemetery, enemies, 
                action=action
            )
            youract, enemies, cemetery = self.turn(
                enemies, cemetery, 
                action=mini.choice(["attack", "heal"]
            )) 

            embed = discord.Embed(title=f"you {action}!", description="")
            desc = "you " + myact + "\n" + "enemy " + youract + "\n\n"
            data = {"cemetery": cemetery, "enemies": enemies}
            for x in data:
                if data[x][0]["health"] <= 0:
                    val = mini.value(data[x][0]["genes"]) * (data["upgrades"]["rp1+"] + 1)
                    desc += ("you" if x == "cemetery" else "an enemy") + f" died. "
                    desc += (f"(and you got {val} research points!)" if x != "cemetery" else "") + "\n" 
                    maing["currency"]["researchpoints"] += val
                    data[x] = data[x][1:]
                    if x == "cemetery":
                        maing[x] = maing[x][1:]
            mini.exdata(maing, id=self.id)
            mini.exdata(data, id=self.id, game=True)
            embed.description = desc
            await interaction.followup.send(embed=embed, ephemeral=True)

            gdata = mini.imdata(self.id, game=True)
            cemetery, enemies = gdata["cemetery"], gdata["enemies"]
            user = interaction.user
            embed = discord.Embed(
                title=f"{user.display_name} ({user.name})'s afterlife research :skull:"
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
                mini.exdata({"cemetery": [], "enemies": []}, id=self.id, game=True)
                return
            for warrior in battlefield:
                fighterobj = battlefield[warrior]
                left = len(gdata[list(gdata.keys())[list(battlefield.keys()).index(warrior)]])
                embed.add_field(
                    name=warrior, 
                    value=f"{left} left\n{mini.emojify(fighterobj['genes'])}\n"
                    + f":punch: {fighterobj['attack']}\n:heart: {fighterobj['health']}") 
            try:
                msg = gamemsg[self.id]
                await msg.edit(embed=embed, view=afterlifeview(self.id))
            except:
                msg = await interaction.followup.send(embed=embed, view=afterlifeview(self.id))
                gamemsg[self.id] = msg
            gdata = {"cemetery": cemetery, "enemies": enemies}
            mini.exdata(gdata, id=self.id, game=True)

    @discord.ui.button(label="attack",style=discord.ButtonStyle.green)
    async def attack(self, interaction, button):
        if interaction.user.id == self.id:
            await self.action("attack", interaction)

    @discord.ui.button(label="heal",style=discord.ButtonStyle.green)
    async def heal(self, interaction, button):
        if interaction.user.id == self.id:
            await self.action("heal", interaction)

# the main game
@bot.tree.command(name="population", description="see your population")
async def population(
    interaction, 
    bottomfirst: Optional[bool], 
    sort_by_serial: Optional[bool], 
    full: Optional[bool] = False
):
    mini.autodie(interaction.user.id)

    await interaction.response.defer()

    mini.log("population", interaction) 

    population = mini.user(interaction.user.id).population
    population = list(sorted(
        population, 
        key=lambda x: 
            x.serial if sort_by_serial else - mini.value(x.genes)
    ))  
    if bottomfirst:
        population = list(reversed(population))

    vessels = [
        population[25*x:min(25*(x+1), len(population))] 
        for x in range(math.ceil(len(population)/25))
    ]       
    embeds = []
    user = interaction.user
    for x in range(len(vessels)):
        embeds.append(discord.Embed(
            title=f"{user.display_name} ({user.name})'s population :people_holding_hands:",
            description=f"page {x+1} of {len(vessels)}"
        ))       
        for p in vessels[x]:
            embeds[-1].add_field(
                name=f"vessel {p.serial} ({mini.emojify(p.genes)})", 
                value=f"parents: {', '.join([str(p) for p in p.parents])}\n" 
                + f"death {format_timestamp(p.deathtime, TimestampType.RELATIVE)}"  
            )       
    
    if not full:
        embeds = [embeds[0]]
        
    while sum(mini.embedlen(e) for e in embeds) > 6000:
        embeds = embeds[:-1]

    await interaction.followup.send(embeds=embeds)

@bot.tree.command(name="hatchery", description="hatchery")
async def hatchery(interaction):
    mini.autodie(interaction.user.id)

    global egg
    await interaction.response.defer()

    mini.log("hatchery", interaction) 

    data = mini.user(interaction.user.id)

    hatchery = data.hatchery
    population = data.population
    registered = data.registered
    limit = data.level
    
    for egg in hatchery:
        try:
            get(egg.hatchtime)
       	except:
            egg.hatchtime = arrow.Arrow.now()

    try:
        nextegg = max(get(egg.hatchtime) for egg in hatchery)           
        nextegg = arrow.Arrow.now() + timedelta(seconds=5*limit * (100-data.upgrades["hwt5-"]*5) / 100)
    except:
        nextegg = arrow.Arrow.now()

    while len(hatchery) < limit + 1:
        parents = mini.parentsample(population)
        genes = mini.newgenes(
            *[p.genes for p in parents],
            upgrade=data.upgrades["mc5+"]
        ) 
        hatchery.append(mini.egg(
            registered+1, list(sorted([p.serial for p in parents])), nextegg, 
            genes=genes[0], mutation=genes[1]
        )) 
        nextegg += timedelta(seconds=5*limit*(100-data.upgrades["hwt5-"]*5)/100)
        registered += 1

    user = interaction.user
    embed = discord.Embed(
        title=f"{user.display_name} ({user.name})'s hatchery :egg:", 
        description=f"{limit+1} eggs"
    )

    for x in range(limit+1):
        try:
            e = hatchery[x]
            embed.add_field(
                name=f"slot {x+1}" 
                + (" :hatching_chick:" if e.hatchtime < arrow.Arrow.now() else " :egg:"), 
                value=f"**vessel {e.serial}\n"
                + f"mutations: {e.mutation}**\n"
                + f"parents: {e.parents[0]}, {e.parents[1]}\n"
                + f"hatching {format_timestamp(e.hatchtime, TimestampType.RELATIVE)}" 
            )
        except:
            pass

    await interaction.followup.send(embed=embed, view=mini.hatcheryview(user.id)) 
 
    data = mini.imdata(interaction.user.id)
    data["hatchery"] = hatchery
    data["registered"] = registered
    mini.exdata(data, id=interaction.user.id)

# population control
@bot.tree.command(name="frickery", description="frickery")
async def frickery(interaction, vessel1: str, vessel2: str, times: str):
    mini.autodie(interaction.user.id)

    await interaction.response.defer()

    mini.log("frickery", interaction) 

    data = mini.imdata(id=interaction.user.id)
    discovered = max(mini.alpha.index(x) for y in data["discovered"] for x in y)
    parents = [vessel1, vessel2] 
    try:
        parents = [
            (
                int(parents[x]) if parents[x] != "max" 
                else sorted(
                    data["population"], key=lambda p: -mini.value(p["genes"])
                )[x]["serial"] 
            )
        for x in range(2)] 
        parents = [
            [x for x in data["population"] if x["serial"] == p][0] 
        for p in parents] 
    except:
        await interaction.followup.send(embed=mini.error_embed("serial numbers"))
        return
    ncoins = 0
    newg = []
    children = []
    embeds = [discord.Embed(title="frickery complete! :baby_chick:")]
    price = 5 * data["level"] * (100-data["upgrades"]["fp5-"]*5)/100

    if times == "max":
        atimes = math.floor(
            data["currency"]["coins"]/(5*data["level"]
            * (100-data["upgrades"]["fp5-"]*5)/100)
        ) 
        if atimes == 0:
            await interaction.followup.send(
                embed=mini.error_embed(
                    "coins", 
                    need=(5*data["level"] * (100-data["upgrades"]["fp5-"]*5)/100)
                )
            ) 
            return
    else:
        try:
            atimes = min(
                math.floor(data["currency"]["coins"] / (5*data["level"])), 
                int(times)
            ) 
        except:
            await interaction.followup.send(embed=mini.error_embed("times"))
            return

    data["currency"]["coins"] -= atimes * price

    atimes = min(atimes, 250)

    for x in range(atimes):
        genes = mini.newgenes(
            *[p["genes"] for p in parents], 
            upgrade=data["upgrades"]["mc5+"]
        ) 
        new = mini.egg(
            data["registered"]+1, 
            list(sorted([p["serial"] for p in parents])), 
            arrow.Arrow.now(), 
            genes=genes[0], mutation=genes[1]
        ) 
        data["population"].append(mini.vessel(new.serial, new.parents, genes=new.genes))
        data["registered"] += 1
        children.append(new)
        ncoins += sum([mini.value(g) for g in new.genes])
        if new.genes not in data["discovered"]:
            data["discovered"].append(new.genes)
            newg.append(new.genes)

    embeds.append(discord.Embed(
        title=f"offspring of parents {', '.join(str(p['serial']) for p in parents)}", 
        description=f"page {1} of {math.ceil(len(children)/25)}"
    )) 
    for x in range(len(children)): 
        new = children[x] 
        nname = f':baby: vessel {new.serial} {mini.emojify(new.genes)}'
        ndesc = f'\n**mutations: {new.mutation}**'
        if sum(mini.embedlen(embed) for embed in embeds) + len(nname + ndesc) >= 6000: 
            break
        else:
            enfields = len(embeds[-1].fields) == 25
            if enfields or mini.embedlen(embeds[-1]) + len(nname + ndesc) >= 6000: 
                embeds.append(discord.Embed(
                    title=f"offspring", 
                    description=f"page {len(embeds)+1} of {math.ceil(len(children)/25)}"
                )) 
            embeds[-1].add_field(name=nname, value=ndesc)

    embeds[0].description = f"you collected {atimes} eggs and got {ncoins} coins.\n" 
    if len(newg) == 0:
        embeds[0].description += "no new combos found."
    else:
        embeds[0].description += "new combos: " + ", ".join(newg)

    data["totalvessels"] += atimes 
    initlevel = data["level"]
    while (data["level"] + 1) * (data["level"] + 2) / 2 <= len(data["discovered"]):
        data["level"] += 1
    data["hatchery"] = [
        e for e in data["hatchery"] 
        if get(e["hatchtime"]) >= arrow.Arrow.now()
    ] 
    data["lastegg"] = arrow.Arrow.now()
    data["currency"]["coins"] += ncoins

    await interaction.followup.send(embeds=embeds[:min(10, len(embeds))])
    mini.exdata(data, id=interaction.user.id)
    if data["level"] != initlevel:
        await interaction.followup.send(embed=discord.Embed(
            title="level up!",
            description=f"you've leveled up to level {data['level']}!"
        ))

    ndiscovered = max(mini.alpha.index(x) for y in data["discovered"] for x in y)
    if ndiscovered < discovered:
        await interaction.followup.send(
            embed=mini.unlock(mini.alpha[ndiscovered]), 
            ephemeral=True
        ) 

@bot.tree.command(name="selection", description="selection")
async def selection(interaction, gene: str):
    mini.autodie(interaction.user.id)

    await interaction.response.defer()

    mini.log("frickery", interaction)
    
    data = mini.imdata(id=interaction.user.id)
    
    discovered = max(mini.alpha.index(x) for y in data["discovered"] for x in y) 
    print(discovered)

    sel = 5 - data["upgrades"]["sl1-"]

    try:
        pos = mini.alpha.index(gene)
    except:
        if gene != "max":
            await interaction.followup.send(embed=mini.error_embed("genes"))
            return
    else:
        if discovered < sel:
            await interaction.followup.send(embed=mini.error_embed("lowgenes"))
            return
        elif discovered - pos < sel:
            await interaction.followup.send(embed=mini.error_embed("highgenes"))
            return

    try:
        if gene == "max":
            remove = discovered - sel
        else:
            remove = max(discovered - sel, mini.alpha.index(gene))
    except:
        await interaction.followup.send("ha you thought")
    else:
        sizes = {p: len(data[p]) for p in ["population", "hatchery"]}
        for p in ["population", "hatchery"]:
            ndata = []
            for vessel in data[p]:
                rmable = [mini.alpha.index(x) <= remove for x in vessel["genes"]]
                if rmable.count(True) != len(rmable):
                    ndata.append(vessel)
            data["cemetery"] += [x for x in data[p] if x not in ndata]
            data[p] = ndata
        skpoints = sum(sizes[x] - len(data[x]) for x in sizes) * (data["upgrades"]["rp1+"] + 1)
        rm = mini.alpha[remove]
        await interaction.followup.send(embed=discord.Embed(
            title = f"(un)natural selection :skull: (both genes {rm} and below)", 
            description = f"you got {skpoints} research points.\n" 
            + "\n".join([f"{x}: {sizes[x]} :arrow_right: {len(data[x])}" for x in sizes]) 
        ))
        data["currency"]["researchpoints"] += skpoints
        mini.exdata(data, id=interaction.user.id)

        ndiscovered = max(mini.alpha.index(x) for y in data["discovered"] for x in y)
        if ndiscovered < discovered:
            await interaction.followup.send(
                embed=mini.unlock(mini.alpha[ndiscovered]), 
                ephemeral=True
            ) 

# dormant vessels
@bot.tree.command(name="cemetery", description="view your cemetery")
async def cemetery(
    interaction, 
    bottomfirst: Optional[bool], 
    sort_by_serial: Optional[bool], 
    full: Optional[bool] = False
): 
    mini.autodie(interaction.user.id)

    await interaction.response.defer()

    mini.log("cemetery", interaction)

    cemetery = mini.user(interaction.user.id).cemetery
    cemetery = list(sorted(
        cemetery, 
        key=lambda x: x.serial if sort_by_serial else -mini.value(x.genes)
    )) 
    if bottomfirst:
        cemetery = list(reversed(cemetery))

    vessels = [
        cemetery[25*x:min(25*(x+1), len(cemetery))] 
        for x in range(math.ceil(len(cemetery)/25))
    ] 
    embeds = []
    for x in range(len(vessels)):
        embeds.append(discord.Embed(
            title=f"{interaction.user.display_name} ({interaction.user.name})'s"
            + "cemetery :people_holding_hands:", 
            description=f"page {x+1} of {len(vessels)}"
        )) 
        for p in vessels[x]:
            embeds[-1].add_field(
                name=f"vessel {p.serial} ({mini.emojify(p.genes)}) :skull:", 
                value=f"parents: {', '.join([str(x) for x in p.parents])}" 
            ) 
    
    if not full:
        embeds = [embeds[0]]

    await interaction.followup.send(embeds=embeds)

@bot.tree.command(name="afterlife", description="research the dormant vessels")
async def afterlife(interaction):
    mini.autodie(interaction.user.id)
    
    await interaction.response.defer()

    mini.log("afterlife", interaction)

    embed = discord.Embed(
        title="what's after life?", 
        description="what after life nae mame strife"
    ) 

    await interaction.followup.send(
        embed=embed, 
        view=afterlifestart(interaction.user.id)
    ) 

# upgrade commands
@bot.tree.command(name="upgrades", description="buy some upgrades")
async def upgrades(interaction):
    mini.autodie(interaction.user.id)

    await interaction.response.defer()

    mini.log("upgrades", interaction)

    data = mini.imdata(id=interaction.user.id)
    researchpoints = data['currency']['researchpoints']

    embed = discord.Embed(
        title=f"{interaction.user.display_name} ({interaction.user.name})'s upgrades", 
        description=f"welcome to the upgrade shop!\nyou have {researchpoints} research points."
        + f"\nyou get {data['upgrades']['rp1+'] + 1} research points per vessel."
    ) 

    for u in data["upgrades"]:
        count = data['upgrades'][u]
        embed.add_field(
            name=f"{u}", 
            value=f"**{mini.upgs[u][0]}**\n"
            + f"currently {u[-1]}{count*5}%\n"
            + f"next {u[-1]}{(count+1)*5}%\n"
            + f"costs {5**count} research points"
        ) 

    await interaction.followup.send(
        embed=embed, 
        view=mini.upgradeview(interaction.user.id)
    ) 

# profile commands
@bot.tree.command(name="me", description="view your profile and stats")
async def profile(interaction):
    mini.autodie(interaction.user.id)

    await interaction.response.defer()

    mini.log("me", interaction)
    
    data = mini.imdata(id=interaction.user.id)

    bio = data["profile"]["bio"]

    if bio == "":
        bio = "you have not picked a bio.\n"
        bio += "use `/editprofile` to add a bio to your account." 

    image = data["profile"]["image"]

    embed = discord.Embed(
        title=f"{interaction.user.display_name} ({interaction.user.name})'s profile", 
        description=f"{bio}"
    ) 
   
    embed.set_thumbnail(url=interaction.user.avatar)
    embed.set_image(url=image)

    for x in ["level", "total vessels"]:
        embed.add_field(name=x, value=data["".join([y for y in x if y != " "])])

    for c in ["coins", "researchpoints"]:
        embed.add_field(
            name=c, 
            value=data["currency"][
                "".join([y for y in c if y != " "])
            ]
        ) 
    embed.add_field(name="population", value=len(data["population"]))
    embed.add_field(name="discovered", value=len(data["discovered"]))
    sortedgenes = sorted(
        data["discovered"],
        key=lambda x: (-mini.value(x), -min(mini.value(y) for y in x))
    ) 
    sortedgenes = [
        mini.emojify(x) for x in sortedgenes 
        if mini.value(x) == mini.value(sortedgenes[0])
    ] 
    embed.add_field(name="highest discovered", value=", ".join(sortedgenes))

    embed2 = discord.Embed(
        title=f"{interaction.user.display_name} ({interaction.user.name})'s numbers", 
        description="just some little stats hehe"
    ) 

    embed2.add_field(
        name="level-based", 
        value="multipliers based solely on your level", 
        inline=False
    ) 
    embed2.add_field(name="number of slots", value=data["level"]+1)
    embed2.add_field(name="base time taken for each egg (s)", value=data["level"]*5)
    embed2.add_field(name="base frickery price", value=data["level"]*5)

    embed2.add_field(
        name="upgrade-based", 
        value="multipliers based on your upgrades", 
        inline=False
    ) 
    for u in data["upgrades"]:
        embed2.add_field(name=u, value=f"{mini.upgs[u][1]} {data['upgrades'][u]*5}%")

    await interaction.followup.send(embeds=[embed, embed2])

@bot.tree.command(name="editprofile", description="update your profile.") 
async def editprof(interaction, updating: str, newvalue: str):
    mini.autodie(interaction.user.id)

    await interaction.response.defer()

    mini.log("editprofile", interaction)

    data = mini.imdata(id=interaction.user.id)    
    
    if updating in ["bio", "image"]:
        data["profile"][updating] = newvalue
        mini.exdata(data, id=interaction.user.id)
        embed = discord.Embed(
            title=f"your new {updating}!", 
            description=(
                f"your {updating} has been set to ```{newvalue}```" 
                if updating == "bio" 
                else f"your {updating} has been updated!"
            ) 
            + "\ncheck `/me` to see how it looks!") 
    else:
        await interaction.followup.send(embed=mini.error_embed("variable"))
        return

    await interaction.followup.send(embed=embed)

    mini.exdata(data, id=interaction.user.id)

@bot.event
async def on_ready():
    print(f'{bot.user} is online.')
    print(f'in {len(bot.guilds)} servers')
    for x in bot.guilds:
        print(f'connected to {x.name}')
    print()
    await bot.setup_hook()

bot.run(TOKEN)

