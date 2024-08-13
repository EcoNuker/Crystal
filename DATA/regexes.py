# WARNING. This document may contain sensitive regexes that include swearing and slurs. Read at your own risk.
import re2

import unicodedata

import json

seperators = r"[\s\-\*.,_\+=!`:;#'\"|$%^&()1234567890" + "".join(
    chr(c) for c in range(0x2000, 0x2050)
)  # U+2000 to U+204F


def helper_string_to_unicode(unicode_list):
    # Converts inputs from https://www.babelstone.co.uk/Unicode/whatisit.html to Python understandable unicode.
    # U+1FBF2 : SEGMENTED DIGIT TWO -> \U0001FBF2
    if type(unicode_list) != list:
        unicode_list = unicode_list.splitlines()
    unique_chars = set()
    for item in unicode_list:
        if item.strip() == "":
            continue
        code_point = item.split()[0].strip()
        zeros = 10 - len(code_point)
        code_point = code_point.replace("+", "0" * zeros)
        if code_point not in unique_chars:
            unique_chars.add(code_point)
    return "\\" + "\\".join(unique_chars)


class chars:
    def __init__(self):

        self.doubled_chars = {
            "*": "\U0001031F",
            "+": "\U0001029B",
            "/": "\U0001D23A",
            "\\": "\U0001D20F\U0001D23B",
            "<": "\U0001D234\U0001D236",
            ">": "\U00016F3F\U0001D233\U0001D237",
        }

        with open("./DATA/data/confusables.json", "r", encoding="utf-8") as f:
            self.char_swaps = {}
            confusables: dict = json.load(f)
            for char, values in confusables.copy().items():
                self.char_swaps[char.lower()] = [char.lower()]
                for confusable in values:
                    # WHY TF IS UNICODE SO ANNOYING RAHHHHHHHHHHHH :dead: (All of these characters are ONE unicode, but count as TWO in regex and SOMETIMES python... but one in vscode... AHHH... i hate ZWJ sequences)
                    if len(confusable) == 2 or (
                        not re2.match(f"\\b(?i)[{confusable}]+\\b", confusable)
                    ):
                        # Update the doubled_chars dictionary with the confusable
                        self.doubled_chars[char.lower()] = self.doubled_chars.get(
                            char.lower(), []
                        )
                        self.doubled_chars[char.lower()].append(confusable)
                    else:
                        self.char_swaps[char.lower()].append(confusable)
        self.chars_other_langs = {
            "A": "人入八凡爪个",
            "B": "日目冒臣曰白百",
            "C": "匚亡了",
            "D": "口回囗团图国",
            "E": "巨巳巴己巳已彐彑",
            "F": "下不厂广天干丰丰幺丆丱",
            "G": "匚卝工巩",
            "H": "廾井川艮艮丰丰",
            "I": "丨丄丅个",
            "J": "亅卜了丁",
            "K": "长片丬开",
            "L": "儿几乚厂",
            "M": "从山巛巫艸",
            "N": "冂巾币市",
            "O": "口日回国囗团图ロ",
            "P": "尸戸戶广广广",
            "Q": "囗田囚圂",
            "R": "尺弓广广广",
            "S": "乂刁幺巳巴己巳已",
            "T": "丁士土丰丄干",
            "U": "凵凶凶岂乇凶元",
            "V": "乇八人入个入",
            "W": "山巛巜艸",
            "X": "乂义交火",
            "Y": "丫叉半个于个个于",
            "Z": "乙之了孑",
            "0": "〇口囗ロ",
        }
        for key, values in self.chars_other_langs.items():
            key = key.lower()
            self.char_swaps[key] = list(set(self.char_swaps.get(key, []) + [*values]))

        self.leetspeak = {}

        self.leetspeak = {
            "a": self.get_char("4"),
            "b": self.get_char("6") + self.get_char("8"),
            "q": self.get_char("9"),
            "e": self.get_char("3"),
            "g": self.get_char("9"),
            "t": self.get_char("7"),
            "l": self.get_char("7"),
            "y": self.get_char("7"),
            "o": self.get_char("0"),
            "l": self.get_char("1") + self.get_char("7"),
            "i": self.get_char("1"),
            "s": self.get_char("5"),
            "z": self.get_char("2"),
        }

    def replace_doubled_chars(self, input: str) -> str:
        for key, values in self.doubled_chars.items():
            for char in values:
                input = input.replace(char, key)
        return input

    def get_char(self, c: str, include_leetspeak: bool = False) -> str:
        char_swaps = self.char_swaps.copy()
        leetspeak = self.leetspeak.copy()
        if include_leetspeak:
            for key, values in leetspeak.items():
                key = key.lower()
                char_swaps[key] = list(set(char_swaps.get(key, []) + [*values]))
        return "".join(char_swaps.get(c.lower(), ""))

    def attempt_clean_zalgo(self, input: str) -> str:
        pattern = re2.compile(r"[^\x{0300}-\x{036F}\x{0489}]+")
        # Apply the pattern to the input_text and join the matches
        result = "".join(pattern.findall(input))
        return result


CHARS = chars()


def generate_regex(
    input: str, plural: bool = False, include_leetspeak: bool = False
) -> str:
    """
    Generate a regex expression with matching for char replacements!

    plural - handles y -> ies cases, and normal s

    include_leetspeak - handles leetspeak. FALSE POSITIVE WARNING! Make sure match is less than 70% numbers. For reliability, use 60%
    """
    pluralized_regex = ""
    if plural:
        if input.endswith("y"):
            pluralized_regex += f"([{CHARS.get_char('i', include_leetspeak=include_leetspeak)}]+[{CHARS.get_char('e', include_leetspeak=include_leetspeak)}]+[{CHARS.get_char('s', include_leetspeak=include_leetspeak)}{CHARS.get_char('z', include_leetspeak=include_leetspeak)}]*)?"
        else:
            pluralized_regex += f"[{CHARS.get_char('s', include_leetspeak=include_leetspeak)}{CHARS.get_char('z', include_leetspeak=include_leetspeak)}]*"
    input = re2.escape(input.lower())  # Escape all characters in input

    def replace_char(c, i):
        if i == len(input) and plural and input.endswith("y"):
            return f"[{CHARS.get_char(c, include_leetspeak=include_leetspeak)}]*"
        else:
            return f"[{CHARS.get_char(c, include_leetspeak=include_leetspeak)}]+"

    # Apply character swaps and make regex case insensitive
    regex = "".join(replace_char(c, i) for i, c in enumerate([*input]))
    # Ensure case insensitivity
    return f"\\b(?i){regex}{pluralized_regex}\\b"


def allow_seperators(regex: str) -> str:
    regex = re2.sub(
        r"([^\\])\*", lambda match: f"{match.group(1)}*[{seperators}]*", regex
    )
    regex = re2.sub(
        r"([^\\])\+", lambda match: f"{match.group(1)}+[{seperators}]*", regex
    )

    def replace_match(match):
        # Extract the matched content
        matched_text = match.group(1)

        # Find the position of the match in the original regex
        start = match.start(1)
        end = match.end(1)

        # Check if the next character is + or *
        if end < len(regex) and regex[end] in "+*":
            return matched_text  # Do not replace if followed by + or *
        else:
            return f"{matched_text}[{seperators}]*"

    regex = re2.sub(r"(\[.*?\])", replace_match, regex)

    o_regex = regex
    regex = [*regex]

    if o_regex.startswith("\\b(?i)"):
        s_insert_position = 6
    elif o_regex.startswith("\\b"):
        s_insert_position = 2
    elif o_regex.startswith("(?i)"):
        s_insert_position = 4
    else:
        s_insert_position = 0

    regex.insert(s_insert_position, f"[{seperators}]*")

    if o_regex.endswith("\\b"):
        e_insert_position = -2
    else:
        e_insert_position = len(regex)  # Absolute end

    regex.insert(e_insert_position, f"[{seperators}]*")

    regex = "".join(regex)

    return regex


slurs = [
    allow_seperators(
        f"(?i)([{CHARS.get_char('s', include_leetspeak=True)}][{CHARS.get_char('a', include_leetspeak=True)}][{CHARS.get_char('h', include_leetspeak=True)}][{CHARS.get_char('d', include_leetspeak=True)}])*([{CHARS.get_char('n', include_leetspeak=True)}]+|[{CHARS.get_char('w', include_leetspeak=True)}]+[{CHARS.get_char('h', include_leetspeak=True)}]*)+[{CHARS.get_char('i', include_leetspeak=True)}{CHARS.get_char('o', include_leetspeak=True)}{CHARS.get_char('a', include_leetspeak=True)}]*[{CHARS.get_char('g', include_leetspeak=True)}]+[{CHARS.get_char('g', include_leetspeak=True)}]+([{CHARS.get_char('e', include_leetspeak=True)}{CHARS.get_char('a', include_leetspeak=True)}]*[{CHARS.get_char('r', include_leetspeak=True)}]+|[{CHARS.get_char('a', include_leetspeak=True)}{CHARS.get_char('e', include_leetspeak=True)}]+[{CHARS.get_char('r', include_leetspeak=True)}]*)+[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}{CHARS.get_char('h', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"(?i)([{CHARS.get_char('n', include_leetspeak=True)}]+|[{CHARS.get_char('w', include_leetspeak=True)}]+[{CHARS.get_char('h', include_leetspeak=True)}]*)+([{CHARS.get_char('e', include_leetspeak=True)}]|[{CHARS.get_char('i', include_leetspeak=True)}])+[{CHARS.get_char('g', include_leetspeak=True)}]+(([{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('o', include_leetspeak=True)}]+)|([{CHARS.get_char('l', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+[{CHARS.get_char('t', include_leetspeak=True)}]+)|([{CHARS.get_char('n', include_leetspeak=True)}]+[{CHARS.get_char('o', include_leetspeak=True)}]+[{CHARS.get_char('g', include_leetspeak=True)}]+[{CHARS.get_char('a', include_leetspeak=True)}]*))[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('t', include_leetspeak=True)}]+[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('a', include_leetspeak=True)}]+[{CHARS.get_char('n', include_leetspeak=True)}]+([{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+|[{CHARS.get_char('y', include_leetspeak=True)}]+|[{CHARS.get_char('e', include_leetspeak=True)}]+[{CHARS.get_char('r', include_leetspeak=True)}]+)[{CHARS.get_char('z', include_leetspeak=True)}{CHARS.get_char('s', include_leetspeak=True)}]*"
    ),
    allow_seperators(
        f"(?i)[{CHARS.get_char('f', include_leetspeak=True)}]+(([{CHARS.get_char('a', include_leetspeak=True)}]*[{CHARS.get_char('g', include_leetspeak=True)}]+([{CHARS.get_char('g', include_leetspeak=True)}{CHARS.get_char('i', include_leetspeak=True)}]*[{CHARS.get_char('o', include_leetspeak=True)}]*[{CHARS.get_char('t', include_leetspeak=True)}]+([{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('y', include_leetspeak=True)}]+|[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+)?|([{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]))([{CHARS.get_char('s', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+)?)|([{CHARS.get_char('a', include_leetspeak=True)}]+[{CHARS.get_char('g', include_leetspeak=True)}]+))[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('k', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('k', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]([{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('y', include_leetspeak=True)}]+|[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+)?[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('c', include_leetspeak=True)}]+[{CHARS.get_char('h', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('n', include_leetspeak=True)}]+[{CHARS.get_char('k', include_leetspeak=True)}]+[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]*[{CHARS.get_char('t', include_leetspeak=True)}]+[{CHARS.get_char('a', include_leetspeak=True)}]+[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('d', include_leetspeak=True)}]+([{CHARS.get_char('e', include_leetspeak=True)}]+[{CHARS.get_char('d', include_leetspeak=True)}]+)?[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*"
    ),
]

# slurs LIST IN ORDER: - no boundary matching on start unless specified
# (n or wh or w) nigger/nigga + pluralized (double g mandatory to match)
# (n or wh or w) negro/niglet/nignog + pluralized
# tranny + pluralized (double n NOT mandatory to match)
# faggot + faggie
# kike (BOUNDARY MATCHES!)
# chink (BOUNDARY MATCHES!)
# retard/rtard/retarded + pluralized

invites = [
    r"(?i)(?:https?:\/\/)?(?:www.|ptb.|canary.)?(?:dsc\.gg|invite\.gg|discord\.link|(?:discord\.(?:gg|io|me|li|id))|disboard\.org|discord(?:app)?\.(?:com|gg)\/(?:invite|servers))\/[a-z0-9-_]+",
    r"(?i)(?:https?:\/\/)?(?:www\.)?(?:guilded\.(?:gg|com))\/(?:i\/[a-z0-9-_]+|[a-z0-9-_]+)",
    r"(?i)(?:https?:\/\/)?(?:www\.)?(?:revolt\.chat|rvlt\.gg)(?:\/[a-zA-Z0-9_-]+)*",
]

invites_exclusions = {
    "guilded": [
        "/TheGG",
        "/Guilded-Official",
        "/EcoNuker",
        "/API-Official",
        "/api",
        "/u",
    ],
    "discord": [],
    "revolt": ["/posts", "/tracker"],
}

# invites LIST IN ORDER:
# discord + third-party invites
# guilded invites, with exclusions TODO: not match support.guilded.gg links
# revolt invites TODO: not match support.revolt.chat links

profanity = [
    allow_seperators(
        generate_regex(
            swear_word, include_leetspeak=any(c.isdigit() for c in swear_word)
        )
    )
    for swear_word in """anal
anus
areole
arrse
arse
arsehole
asanchez
ass
assbang
assbanged
asses
assfuck
assfucker
assfukka
asshole
assmunch
asswhole
autoerotic
ballsack
bastard
bdsm
beastial
beastiality
bestial
bestiality
bimbo
bimbos
bitch
bitches
bitchin
bitching
blowjob
blowjobs
bondage
boner
boob
boobs
booty call
breasts
bukake
bukkake
bullshit
chink
cipa
clit
clitoris
clits
cock
cockface
cockhead
cockmunch
cockmuncher
cocks
cocksuck
cocksucked
cocksucker
cocksucking
cocksucks
cokmuncher
cum
cuming
cummer
cumming
cums
cumshot
cunilingus
cunillingus
cunnilingus
cunt
cuntlicker
cuntlicking
cunts
deepthroat
dick
dickhead
dildo
dildos
dog style
dog-fucker
doggiestyle
doggin
dogging
doggystyle
dumass
dumbass
dumbasses
dummy
dyke
dykes
eatadick
eathairpie
ejaculate
ejaculated
ejaculates
ejaculating
ejaculatings
ejaculation
ejakulate
erect
erection
erotic
erotism
extacy
extasy
facial
fag
fagg
fagged
fagging
faggit
faggitt
faggot
faggs
fagot
fagots
fags
faig
faigt
fannyfucker
fanyy
fartknocker
fatass
fcuk
fcuker
fcuking
feck
fecker
felch
felcher
felching
fellate
fellatio
feltch
feltcher
femdom
fingerfuck
fingerfucked
fingerfucker
fingerfuckers
fingerfucking
fingerfucks
fingering
fisted
fistfuck
fistfucked
fistfucker
fistfuckers
fistfucking
fistfuckings
fistfucks
fisting
fisty
flange
flogthelog
floozy
fondle
fook
fooker
footjob
foreskin
freex
frigg
frigga
fubar
fuck
fucka
fuckass
fuckbitch
fucked
fucker
fuckers
fuckface
fuckhead
fuckheads
fuckhole
fuckin
fucking
fuckings
fuckingshitmotherfucker
fuckme
fuckmeat
fucknugget
fucknut
fuckoff
fuckpuppet
fucks
fucktard
fucktoy
fucktrophy
fuckup
fuckwad
fuckwhit
fuckwit
fuckyomama
fudgepacker
fuk
fuker
fukker
fukkin
fukking
fuks
fukwhit
fukwit
futanari
futanary
fux
fuxor
fxck
gangbang
gangbanged
gangbangs
ganja
gassyass
gaysex
goldenshower
gonad
gonads
gook
gooks
gspot
handjob
hardcoresex
hardon
hentai
heroin
hitler
homoerotic
homoey
honky
hooch
hookah
hooker
horniest
horny
hotsex
hump
humped
humping
hussy
hymen
inbred
incest
jackass
jackhole
jackoff
jerked
jerkoff
jism
jiz
jizm
jizz
jizzed
kawk
kike
kikes
kkk
klan
kukluxklan
knob
knobead
knobed
knobend
knobhead
knobjocky
knobjokey
kock
kondum
kondums
kooch
kooches
kootch
kraut
kum
kummer
kumming
kums
kunilingus
kwif
kyke
l3itch
labia
lust
lusting
lusty
m-fucking
mafugly
massa
masterb8
masterbate
masterbating
masterbation
masterbations
masturbate
masturbating
masturbation
menstruate
menstruation
meth
milf
mothafuck
mothafucka
mothafuckas
mothafuckaz
mothafucked
mothafucker
mothafuckers
mothafuckin
mothafucking
mothafuckings
mothafucks
motherfuck
motherfucka
motherfucked
motherfucker
motherfuckers
motherfuckin
motherfucking
motherfuckings
motherfuckka
motherfucks
mtherfucker
mthrfucker
mthrfucking
muthafecker
muthafuckaz
muthafucker
muthafuckker
muther
mutherfucker
mutherfucking
muthrfucking
nazi
nazism
needthedick
negro
nig
nigg
nigga
niggah
niggas
niggaz
nigger
niggers
niggle
niglet
nipple
nipples
organ
orgasim
orgasims
orgasm
orgasmic
orgasms
orgies
orgy
pantie
panties
panty
pedo
pedophile
pedophilia
pedophiliac
penetrate
penetration
penial
penile
penis
penisfucker
perversion
phalli
phallic
phonesex
phuck
phuk
phuked
phuking
phukked
phukking
phuks
phuq
pigfucker
pillowbiter
poop
porn
porno
pornography
pornos
punkass
punky
puss
pusse
pussi
pussies
pussy
pussyfart
pussypalace
pussypounder
pussys
quicky
rape
raped
raper
raping
rapist
reetard
reich
retard
retarded
rimjaw
rimjob
rimming
ritard
rtard
sausagequeen
schlong
seduce
semen
sex
sexual
shag
shagger
shaggin
shagging
shemale
shit
shitdick
shite
shiteater
shited
shitey
shitface
shitfuck
shitfucker
shitfull
shithead
shithole
shithouse
shiting
shitings
shits
shitt
shitted
shitter
shitters
shitting
shittings
shitty
sleaze
sleazy
slope
slut
slutbucket
slutdumper
slutkiss
sluts
smegma
smut
smutty
son-of-a-bitch
sperm
sumofabiatch
teat
teets
teste
testee
testes
testical
testicle
testis
threesome
tit
titfuck
titi
tits
titt
tittiefucker
titties
titty
tittyfuck
tittyfucker
tittywank
titwank
transsexual
urine
uterus
vag
vagina
valium
viagra
vigra
virgin
voyeur
vulva
weed
weenie
weewee
weiner
whoar
whoralicious
whore
whorealicious
whored
whoreface
whorehopper
whorehouse
whores
whoring""".splitlines()
]


if __name__ == "__main__":
    while True:
        inp = input("> ")
        a = generate_regex(inp)
        print(a)
        input("")
        b = allow_seperators(a)
        print(b)
