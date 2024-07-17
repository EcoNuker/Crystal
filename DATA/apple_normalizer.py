from itertools import product


def generate_apple_versions(s):
    replacements = {
        '"': ["“", "”"],
        "'": ["‘", "’"],
        "--": ["–"],
        "---": ["—"],
        "...": ["…"],
    }
    for key in replacements.keys():
        if key not in replacements[key]:
            replacements[key].append(key)
    res = []
    for sub in [
        zip(replacements.keys(), chr) for chr in product(*replacements.values())
    ]:
        temp = s
        for repls in sub:
            temp = temp.replace(*repls)
        res.append(temp)
    f = res[-1]
    del res[-1]
    res.insert(0, f)
    return res
