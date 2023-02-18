import json
import time
import discord
from random import random
from arrow import arrow, get
from datetime import timedelta
from classes import person, egg, fighter

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
