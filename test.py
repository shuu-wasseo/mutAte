from mini import value, evolchance, newgenes, unlock, emojify
import discord

def test(num, tot, x, y, testin=False):
    try:
        if testin:
            cond = x in y
        else:
            cond = x == y
        assert cond, f"should be {y}, instead got {x}" + (f"\n{y.title}, {y.description} != {x.title}, {x.description}" if isinstance(y, discord.Embed) else "")
    except Exception as e:
        raise e
    else:
        print(f"test {num}/{tot} completed")

tests = {
    "mini.value": {
        "func": value,
        "tests": [
            (["Z"], {}, 1),
            (["Y"], {}, 2),
            (["ZZ"], {}, 2),
            (["ZY"], {}, 3),
            (["YY"], {}, 4),
            (["ZX"], {}, 4)
        ]
    },
    "mini.evolchance": {
        "func": evolchance,
        "tests": [
            (["Z"], {}, 0.25),
            (["Y"], {}, 0.24),
            (["X"], {}, 0.23)
        ]
    },
    "mini.newgenes": {
        "func": newgenes,
        "tests": [
            (["ZZ", "YY"], {}, [x+y for x in "XYZ" for y in "XYZ"]) for x in range(9)
        ]
    },
    "mini.unlock": {
        "func": unlock,
        "tests": [
            (["Z"], {}, discord.Embed(
                title=f"you've unlocked {emojify('Z')}!", 
                description="keep grinding!"
            )),
            (["U"], {}, discord.Embed(
                title=f"you've unlocked {emojify('U')}!", 
                description=f"you now can run `/selection` and kill off everyone with {emojify('Z')} or below for both genes."
            )),
            (["T"], {}, discord.Embed(
                title=f"you've unlocked {emojify('T')}!", 
                description=f"you now can run `/selection` again and kill off everyone with {emojify('Y')} or below for both genes."
            )),
            (["A"], {}, discord.Embed(
                title=f"you've unlocked {emojify('A')}!", 
                description="keep grinding!"
            ))
        ]
    }
}

for d, k in tests.items():
    print(f"\ntesting {d}")
    count = 1
    for args, kwargs, y in k["tests"]:
        run = k["func"](*args, **kwargs)
        if (d=="mini.newgenes"):
            run = run[0]
        test(count, len(k["tests"]), run, y, testin=(d=="mini.newgenes"))
        count += 1
