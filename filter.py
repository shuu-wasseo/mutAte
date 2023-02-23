filename = 'mini.py'

with open(filename) as f:
    ols = f.readlines()

ols = [x.strip("\n") for x in ols]
lines = [l.strip().split("#")[0].strip() for l in ols]

count = 0
for l in range(len(lines)):
    if len(lines[l]) > 80:
        print(f"line {l+1} ('{lines[l]}') is too long! ({len(lines[l])} chars)")
        count += 1
        ols[l] = ols[l].split("#")[0].rstrip() + f" # TMC: {len(lines[l])} chars"
    else:
        if "TMC" in ols[l].split("#")[-1]:
            ols[l] = "#".join(ols[l].split("#")[:-1])

total = len([x for x in lines if x != []])
print(f"score: {total-count}/{total}")

f = open(filename, "w")
f.writelines([x + "\n" for x in ols])
f.close()
