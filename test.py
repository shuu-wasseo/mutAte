from mini import value

def test(x, y):
    assert x == y, f"should be {y}, instead got {x}"

tests = {
    "mini.value": [
        (value("Z"), 1),
        (value("Y"), 2),
        (value("ZZ"), 2),
        (value("ZY"), 3),
        (value("YY"), 4),
        (value("ZX"), 4)
    ] 
}

for d, k in tests.items():
    print(f"testing {d}")
    for x, y in k:
        test(x, y)
