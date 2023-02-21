from mini import value, evolchance, newgenes

def test(num, tot, x, y, testin=False):
    try:
        if testin:
            cond = x in y
        else:
            cond = x == y
        assert cond, f"should be {y}, instead got {x}"
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
