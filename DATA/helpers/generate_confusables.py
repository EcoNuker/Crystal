import requests
import json
import unicodedata

# URL to download the confusables.txt file
url = "https://raw.githubusercontent.com/unicode-org/unicodetools/main/unicodetools/data/security/dev/confusables.txt"

# Download the file content
response = requests.get(url)
confusables_data = response.text

# Define combining diacritical marks
combining_diacritical_marks = [
    "\u0300",
    "\u0301",
    "\u0302",
    "\u0303",
    "\u0304",
    "\u0305",
    "\u0306",
    "\u0307",
    "\u0308",
    "\u0309",
    "\u030A",
    "\u030B",
    "\u030C",
    "\u030D",
    "\u030E",
    "\u030F",
    "\u0310",
    "\u0311",
    "\u0312",
    "\u0313",
    "\u0314",
    "\u0315",
    "\u0316",
    "\u0317",
    "\u0318",
    "\u0319",
    "\u031A",
    "\u031B",
    "\u031C",
    "\u031D",
    "\u031E",
    "\u031F",
    "\u0320",
    "\u0321",
    "\u0322",
    "\u0323",
    "\u0324",
    "\u0325",
    "\u0326",
    "\u0327",
    "\u0328",
    "\u0329",
    "\u032A",
    "\u032B",
    "\u032C",
    "\u032D",
    "\u032E",
    "\u032F",
    "\u0330",
    "\u0331",
    "\u0332",
    "\u0333",
    "\u0334",
    "\u0335",
    "\u0336",
    "\u0337",
    "\u0338",
    "\u0339",
    "\u033A",
    "\u033B",
    "\u033C",
    "\u033D",
    "\u033E",
    "\u033F",
    "\u0340",
    "\u0341",
    "\u0342",
    "\u0343",
    "\u0344",
    "\u0345",
    "\u0346",
    "\u0347",
    "\u0348",
    "\u0349",
    "\u034A",
    "\u034B",
    "\u034C",
    "\u034D",
    "\u034E",
    "\u034F",
    "\u0350",
    "\u0351",
    "\u0352",
    "\u0353",
    "\u0354",
    "\u0355",
    "\u0356",
    "\u0357",
    "\u0358",
    "\u0359",
    "\u035A",
    "\u035B",
    "\u035C",
    "\u035D",
    "\u035E",
    "\u035F",
    "\u0360",
    "\u0361",
    "\u0362",
    "\u0363",
    "\u0364",
    "\u0365",
    "\u0366",
    "\u0367",
    "\u0368",
    "\u0369",
    "\u036A",
    "\u036B",
    "\u036C",
    "\u036D",
    "\u036E",
    "\u036F",
]

# Initialize a dictionary to store the results
confusables_dict = {
    char: []
    for char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
}


# Function to add combining diacritical marks and precomposed characters
def add_combining_marks(char):
    variants = []
    for mark in combining_diacritical_marks:
        combined = char + mark
        precomposed = unicodedata.normalize("NFC", combined)
        if combined not in variants:
            variants.append(combined)
        if precomposed not in variants and precomposed != char:
            variants.append(precomposed)
    return variants


# Custom dictionary for subscript and superscript characters, as well as other script letters NOT in confusables (for some reason)
# includes SOME hebrew (maybe up to 10 characters)
# includes all of cherokee/armenian/osage
# working on canadian aboriginal
# working on old italic chars https://www.unicode.org/charts/PDF/U10300.pdf
# working on fullwidth latin characters
# working on latin extended https://unicode.org/charts/PDF/U0180.pdf
# working on Carian https://www.unicode.org/charts/PDF/U102A0.pdf
# TODO: scroll through https://en.wikipedia.org/wiki/Unicode_block and find more... more work

# TODO: handle yi syllabels https://www.unicode.org/charts/PDF/UA000.pdf https://www.unicode.org/charts/PDF/UA490.pdf
# TODO: handle Neo-Tifinagh https://www.unicode.org/charts/PDF/U2D30.pdf
# TODO: handle Greek https://www.unicode.org/charts/PDF/U1F00.pdf https://www.unicode.org/charts/PDF/U0370.pdf
# TODO: handle Thai https://www.unicode.org/charts/PDF/U0E00.pdf
# TODO: handle Cham https://www.unicode.org/charts/PDF/UAA00.pdf
# TODO: handle Limbu https://unicode.org/charts/PDF/U1900.pdf

# NOTE: maybe TODO handle cyrillic https://en.wikipedia.org/wiki/Cyrillic_script
# We're never doing this: handle Chinese
# We're never doing this: handle Kanji
"""
𐊣
𐊤
𐊦
𐊧
𐊨
𐊩
𐊪
𐊬
𐊭
𐊮
𐊯
𐊳
𐊵
𐊶
𐊷
𐊸
𐊹
𐊺
𐊻
𐊼
𐊽
𐊾
𐊿
𐋀
𐋁
𐋂
𐋃
𐋄
𐋅
𐋆
𐋇
𐋈
𐋉
𐋊
𐋋
𐋌
𐋍
𐋎
𐋐
ƀ
Ɓ
Ƃ
ƃ
Ƅ
ƅ
Ɔ
Ƈ
ƈ
Ɖ
Ɗ
Ƌ
ƌ
ƍ
Ǝ
Ə
Ɛ
Ƒ
ƒ
Ɠ
Ɣ
ƕ
Ɩ
Ɨ
Ƙ
ƙ
ƚ
ƛ
Ɯ
Ɲ
ƞ
Ɵ
Ơ
ơ
Ƣ
ƣ
Ƥ
ƥ
Ʀ
Ƨ
ƨ
Ʃ
ƪ
ƫ
Ƭ
ƭ
Ʈ
Ư
ư
Ʊ
Ʋ
Ƴ
ƴ
Ƶ
ƶ
Ʒ
Ƹ
ƹ
ƺ
ƻ
Ƽ
ƽ
ƾ
ƿ
ǀ
ǁ
ǂ
ǃ
Ǆ
ǅ
ǆ
Ǉ
ǈ
ǉ
Ǌ
ǋ
ǌ
Ǎ
ǎ
Ǐ
ǐ
Ǒ
ǒ
Ǔ
ǔ
Ǖ
ǖ
Ǘ
ǘ
Ǚ
ǚ
Ǜ
ǜ
ǝ
Ǟ
ǟ
Ǡ
ǡ
Ǣ
ǣ
Ǥ
ǥ
Ǧ
ǧ
Ǩ
ǩ
Ǫ
ǫ
Ǭ
ǭ
Ǯ
ǯ
ǰ
Ǳ
ǲ
ǳ
Ǵ
ǵ
Ƕ
Ƿ
Ǹ
ǹ
Ǻ
ǻ
Ǽ
ǽ
Ǿ
ǿ
Ȁ
ȁ
Ȃ
ȃ
Ȅ
ȅ
Ȇ
ȇ
Ȉ
ȉ
Ȋ
ȋ
Ȍ
ȍ
Ȏ
ȏ
Ȑ
ȑ
Ȓ
ȓ
Ȕ
ȕ
Ȗ
ȗ
Ș
ș
Ț
ț
Ȝ
ȝ
Ȟ
ȟ
Ƞ
ȡ
Ȣ
ȣ
Ȥ
ȥ
Ȧ
ȧ
Ȩ
ȩ
Ȫ
ȫ
Ȭ
ȭ
Ȯ
ȯ
Ȱ
ȱ
Ȳ
ȳ
ȴ
ȵ
ȶ
ȷ
ȸ
ȹ
Ⱥ
Ȼ
ȼ
Ƚ
Ⱦ
ȿ
ɀ
Ɂ
ɂ
Ƀ
Ʉ
Ʌ
Ɇ
ɇ
Ɉ
ɉ
Ɋ
ɋ
Ɍ
ɍ
Ɏ
ɏ
ᑍ
ᑎ
ᑏ
ᑙ
ᑚ
ᑛ
ᑜ
ᑝ
ᑞ
ᑟ
ᑠ
ᑧ
ᑨ
ᑩ
ᑫ


ᑰ
ᑱ
ᑳ
ᑴ
ᑵ
ᑶ
ᑷ
ᑸ
ᑹ
ᑺ
ᑻ
ᑼ
ᑽ
ᑾ
ᑿ
ᒀ
ᒁ
ᒂ
ᒃ
ᒄ
ᒅ
ᒆ
ᒇ
ᒈ
ᒉ
ᒊ
ᒋ
ᒌ
ᒎ
ᒏ
ᒐ
ᒑ
ᒒ
ᒓ
ᒔ
ᒕ
ᒖ
ᒗ
ᒘ
ᒙ
ᒚ
ᒛ
ᒜ
ᒝ
ᒞ
ᒟ
ᒠ
ᒡ
ᒢ
ᒣ
ᒤ
ᒥ
ᒦ
ᒧ
ᒨ
ᒩ
ᒫ
ᒬ
ᒭ
ᒮ
ᒯ
ᒰ
ᒱ
ᒲ
ᒳ
ᒴ
ᒵ
ᒶ
ᒷ
ᒸ
ᒹ
ᒺ
ᒻ
ᒾ
ᔆ
ᔌ (k? maybe)
ᔎ
ᔏ
ᔐ
ᔑ
ᔒ
ᔓ
ᔔ
ᔕ
ᔖ
ᔗ
ᔘ
ᔙ
ᔚ
ᔛ
ᔜ
ᕂ
ᕃ
ᕄ
ᕅ
ᕆ
ᕇ
ᕈ
ᕉ
ᕊ
ᕋ
ᕌ
ᕍ
ᕎ
ᕏ
ᕓ
ᕔ
ᕕ
ᕖ
ᕗ
ᕘ
ᕙ
ᕚ
ᕛ
ᕜ
ᕝ
ᕞ
ᕟ
ᕠ
ᕡ
ᕢ
ᕣ
ᕤ
ᕥ
ᕦ
ᕧ
ᕨ
ᕩ
ᕪ
ᕫ
ᕬ
ᕭ
ᕮ
ᕰ
ᕱ
ᕲ
ᕳ
ᕴ
ᕸ
ᕹ
ᕺ
ᕻ
ᕾ
ᕿ
ᖀ
ᖁ
ᖂ
ᖃ
ᖄ
ᖅ
ᖆ
ᖈ
ᖉ
ᖊ
ᖋ
ᖌ
ᖍ
ᖰ
ᖱ
ᖲ
ᖳ
ᖶ (l and t)
ᖷ
ᖸ
ᖹ
ᖺ
ᖻ
ᖼ
ᖽ
ᖾ
ᖿ
ᗀ
ᗁ
ᗂ
ᗃ
ᗄ
ᗊ
ᗐ
ᗖ
ᗗ (A)
ᗜ
ᗝ
ᗟ
ᗠ
ᗡ
ᗢ
ᗣ
ᗤ
ᗥ
ᗦ
ᗧ
ᗨ
ᗩ
ᗫ
ᗬ
ᗭ
ᗯ
ᗱ
ᗲ
ᗳ
ᗴ
ᗵ
ᗶ
ᗸ
ᗹ
ᗺ
ᗻ
ᗼ
ᗽ
ᗾ
ᗿ
ᘀ
ᘁ
ᘂ
ᘇ
ᘈ
ᘉ
ᘊ
ᘋ
ᘌ
ᘍ
ᘎ
ᘏ
ᘐ
ᘑ
ᘒ
ᘓ
ᘔ
ᘕ
ᘖ
ᘗ
ᘘ
ᘙ
ᘚ
ᘛ
ᘝ
ᘞ
ᘟ
ᘠ
ᘡ
ᘢ
ᘣ
ᘤ
ᘥ
ᘦ
ᘧ
ᘨ
ᘩ
ᘪ
ᘫ
ᘬ
ᘭ
ᘯ
ᘰ
ᘱ
ᘲ
ᘴ
ᘵ
ᘶ
ᘷ
ᘸ
ᘹ
ᘺ
ᘻ
ᘼ
ᘽ
ᘾ
ᘿ
ᙀ
ᙁ
ᙂ
ᙃ
ᙄ
ᙅ
ᙈ
ᙉ
ᙊ
ᙋ
ᙌ
ᙍ
ᙎ
ᙏ
ᙐ
ᙑ
ᙒ
ᙔ
ᙕ
ᙗ
ᙙ
ᙛ
ᙜ
ᙠ

𐌀
𐌁
𐌂
𐌃
𐌄
𐌅
𐌆
𐌇
𐌈
𐌉
𐌊
𐌋
𐌌
𐌍
𐌎
𐌏
𐌐
𐌑
𐌒
𐌓
𐌔
𐌕
𐌖
𐌗
𐌘
𐌙
𐌚
𐌛
𐌜
𐌝
𐌞
𐌟
𐌠
𐌡
𐌢
𐌣
𐌭
𐌮
𐌯

！	65281	！	FF01	FULLWIDTH EXCLAMATION MARK (THIS IS A 1 / I / L)
＃	65283	＃	FF03	FULLWIDTH NUMBER SIGN (AN H)
＄	65284	＄	FF04	FULLWIDTH DOLLAR SIGN (A S)
０	65296	０	FF10	FULLWIDTH DIGIT ZERO
１	65297	１	FF11	FULLWIDTH DIGIT ONE
２	65298	２	FF12	FULLWIDTH DIGIT TWO
３	65299	３	FF13	FULLWIDTH DIGIT THREE
４	65300	４	FF14	FULLWIDTH DIGIT FOUR
５	65301	５	FF15	FULLWIDTH DIGIT FIVE
６	65302	６	FF16	FULLWIDTH DIGIT SIX
７	65303	７	FF17	FULLWIDTH DIGIT SEVEN
８	65304	８	FF18	FULLWIDTH DIGIT EIGHT
９	65305	９	FF19	FULLWIDTH DIGIT NINE
：	65306	：	FF1A	FULLWIDTH COLON
；	65307	；	FF1B	FULLWIDTH SEMICOLON
＜	65308	＜	FF1C	FULLWIDTH LESS-THAN SIGN
＝	65309	＝	FF1D	FULLWIDTH EQUALS SIGN
＞	65310	＞	FF1E	FULLWIDTH GREATER-THAN SIGN
？	65311	？	FF1F	FULLWIDTH QUESTION MARK
＠	65312	＠	FF20	FULLWIDTH COMMERCIAL AT
Ａ	65313	Ａ	FF21	FULLWIDTH LATIN CAPITAL LETTER A
Ｂ	65314	Ｂ	FF22	FULLWIDTH LATIN CAPITAL LETTER B
Ｃ	65315	Ｃ	FF23	FULLWIDTH LATIN CAPITAL LETTER C
Ｄ	65316	Ｄ	FF24	FULLWIDTH LATIN CAPITAL LETTER D
Ｅ	65317	Ｅ	FF25	FULLWIDTH LATIN CAPITAL LETTER E
Ｆ	65318	Ｆ	FF26	FULLWIDTH LATIN CAPITAL LETTER F
Ｇ	65319	Ｇ	FF27	FULLWIDTH LATIN CAPITAL LETTER G
Ｈ	65320	Ｈ	FF28	FULLWIDTH LATIN CAPITAL LETTER H
Ｉ	65321	Ｉ	FF29	FULLWIDTH LATIN CAPITAL LETTER I
Ｊ	65322	Ｊ	FF2A	FULLWIDTH LATIN CAPITAL LETTER J
Ｋ	65323	Ｋ	FF2B	FULLWIDTH LATIN CAPITAL LETTER K
Ｌ	65324	Ｌ	FF2C	FULLWIDTH LATIN CAPITAL LETTER L
Ｍ	65325	Ｍ	FF2D	FULLWIDTH LATIN CAPITAL LETTER M
Ｎ	65326	Ｎ	FF2E	FULLWIDTH LATIN CAPITAL LETTER N
Ｏ	65327	Ｏ	FF2F	FULLWIDTH LATIN CAPITAL LETTER O
Ｐ	65328	Ｐ	FF30	FULLWIDTH LATIN CAPITAL LETTER P
Ｑ	65329	Ｑ	FF31	FULLWIDTH LATIN CAPITAL LETTER Q
Ｒ	65330	Ｒ	FF32	FULLWIDTH LATIN CAPITAL LETTER R
Ｓ	65331	Ｓ	FF33	FULLWIDTH LATIN CAPITAL LETTER S
Ｔ	65332	Ｔ	FF34	FULLWIDTH LATIN CAPITAL LETTER T
Ｕ	65333	Ｕ	FF35	FULLWIDTH LATIN CAPITAL LETTER U
Ｖ	65334	Ｖ	FF36	FULLWIDTH LATIN CAPITAL LETTER V
Ｗ	65335	Ｗ	FF37	FULLWIDTH LATIN CAPITAL LETTER W
Ｘ	65336	Ｘ	FF38	FULLWIDTH LATIN CAPITAL LETTER X
Ｙ	65337	Ｙ	FF39	FULLWIDTH LATIN CAPITAL LETTER Y
Ｚ	65338	Ｚ	FF3A	FULLWIDTH LATIN CAPITAL LETTER Z
［	65339	［	FF3B	FULLWIDTH LEFT SQUARE BRACKET
＼	65340	＼	FF3C	FULLWIDTH REVERSE SOLIDUS
］	65341	］	FF3D	FULLWIDTH RIGHT SQUARE BRACKET
＾	65342	＾	FF3E	FULLWIDTH CIRCUMFLEX ACCENT
＿	65343	＿	FF3F	FULLWIDTH LOW LINE
｀	65344	｀	FF40	FULLWIDTH GRAVE ACCENT
ａ	65345	ａ	FF41	FULLWIDTH LATIN SMALL LETTER A
ｂ	65346	ｂ	FF42	FULLWIDTH LATIN SMALL LETTER B
ｃ	65347	ｃ	FF43	FULLWIDTH LATIN SMALL LETTER C
ｄ	65348	ｄ	FF44	FULLWIDTH LATIN SMALL LETTER D
ｅ	65349	ｅ	FF45	FULLWIDTH LATIN SMALL LETTER E
ｆ	65350	ｆ	FF46	FULLWIDTH LATIN SMALL LETTER F
ｈ	65352	ｈ	FF48	FULLWIDTH LATIN SMALL LETTER H
ｉ	65353	ｉ	FF49	FULLWIDTH LATIN SMALL LETTER I
ｊ	65354	ｊ	FF4A	FULLWIDTH LATIN SMALL LETTER J
ｋ	65355	ｋ	FF4B	FULLWIDTH LATIN SMALL LETTER K
ｌ	65356	ｌ	FF4C	FULLWIDTH LATIN SMALL LETTER L
ｏ	65359	ｏ	FF4F	FULLWIDTH LATIN SMALL LETTER O
ｐ	65360	ｐ	FF50	FULLWIDTH LATIN SMALL LETTER P
ｑ	65361	ｑ	FF51	FULLWIDTH LATIN SMALL LETTER Q
ｒ	65362	ｒ	FF52	FULLWIDTH LATIN SMALL LETTER R
ｓ	65363	ｓ	FF53	FULLWIDTH LATIN SMALL LETTER S
ｕ	65365	ｕ	FF55	FULLWIDTH LATIN SMALL LETTER U
ｖ	65366	ｖ	FF56	FULLWIDTH LATIN SMALL LETTER V
ｗ	65367	ｗ	FF57	FULLWIDTH LATIN SMALL LETTER W
ｘ	65368	ｘ	FF58	FULLWIDTH LATIN SMALL LETTER X
ｙ	65369	ｙ	FF59	FULLWIDTH LATIN SMALL LETTER Y
ｚ	65370	ｚ	FF5A	FULLWIDTH LATIN SMALL LETTER Z
｛	65371	｛	FF5B	FULLWIDTH LEFT CURLY BRACKET
｜	65372	｜	FF5C	FULLWIDTH VERTICAL LINE
｝	65373	｝	FF5D	FULLWIDTH RIGHT CURLY BRACKET
～	65374	～	FF5E	FULLWIDTH TILDE
｡	65377	｡	FF61	HALFWIDTH IDEOGRAPHIC FULL STOP
｢	65378	｢	FF62	HALFWIDTH LEFT CORNER BRACKET
｣	65379	｣	FF63	HALFWIDTH RIGHT CORNER BRACKET
￠	65504	￠	FFE0	FULLWIDTH CENT SIGN
￡	65505	￡	FFE1	FULLWIDTH POUND SIGN
￢	65506	￢	FFE2	FULLWIDTH NOT SIGN
￣	65507	￣	FFE3	FULLWIDTH MACRON
￤	65508	￤	FFE4	FULLWIDTH BROKEN BAR
￥	65509	￥	FFE5	FULLWIDTH YEN SIGN
￦	65510	￦	FFE6	FULLWIDTH WON SIGN
￨	65512	￨	FFE8	HALFWIDTH FORMS LIGHT VERTICAL
￩	65513	￩	FFE9	HALFWIDTH LEFTWARDS ARROW
￪	65514	￪	FFEA	HALFWIDTH UPWARDS ARROW
￫	65515	￫	FFEB	HALFWIDTH RIGHTWARDS ARROW
￬	65516	￬	FFEC	HALFWIDTH DOWNWARDS ARROW
￭	65517	￭	FFED	HALFWIDTH BLACK SQUARE
￮	65518	￮	FFEE	HALFWIDTH WHITE CIRCLE
"""
custom_dict = {
    # \/ Lower case \/
    "a": ["ᵃ", "ₐ", "⒜", "ⓐ", "@", "ᣲ", "𐓯", "𐒷", "𐒸", "𐓟", "𐓠", "𐓇"],
    "b": ["ᵇ", "⒝", "ⓑ", "𐓭", "𐓬", "𐓄", "𐓅"],
    "c": ["ᶜ", "⒞", "ⓒ", "Ꮸ", "¢", "𐓮", "𐒿", "𐓧", "𐓆"],
    "d": ["ᵈ", "⒟", "ⓓ", "Ꮄ", "ծ", "ձ", "ժ", "Ժ"],
    "e": ["ᵉ", "ₑ", "⒠", "ⓔ"],
    "f": ["ᶠ", "⒡", "ⓕ", "բ", "Բ", "⨍", "𐒹", "𐒺", "𐓡", "𐓢"],
    "g": ["ᵍ", "⒢", "ⓖ", "ｇ"],
    "h": ["ʰ", "ₕ", "⒣", "ⓗ", "Ꮵ", "ի", "ᑋ", "𐓍"],
    "i": ["ⁱ", "ᵢ", "⒤", "ⓘ", "וֹ", "𐒹", "𐒺", "𐓡", "𐓢"],
    "j": ["ʲ", "⒥", "ⓙ", "յ", "𐒹", "𐒺", "𐓡", "𐓢"],
    "k": ["ᵏ", "ₖ", "⒦", "ⓚ"],
    "l": ["ˡ", "ₗ", "⒧", "ⓛ", "ᣳ", "𐒹", "𐒺", "𐓡", "𐓢"],
    "m": ["ᵐ", "ₘ", "⒨", "ⓜ", "ՠ", "𐓐", "ｍ"],
    "n": [
        "ⁿ",
        "ₙ",
        "⒩",
        "ⓝ",
        "ր",
        "ղ",
        "ը",
        "դ",
        "Ռ",
        "Ո",
        "Թ",
        "ת",
        "Ꮑ",
        "𐒵",
        "𐒶",
        "𐒻",
        "ｎ",
        "𐓣",
        "𐓝",
        "𐓞",
    ],
    "o": ["ᵒ", "ₒ", "⒪", "ⓞ", "ծ", "ձ", "Փ", "Ծ", "ᐤ", "☯", "𐓫", "𐓃"],
    "p": ["ᵖ", "ₚ", "⒫", "ⓟ", "թ", "ᣖ", "𐓌", "𐓋", "𐓊"],
    "q": ["ᑫ", "⒬", "ⓠ"],
    "r": [
        "ʳ",
        "ᵣ",
        "⒭",
        "ⓡ",
        "Ꮅ",
        "Ꮁ",
        "ր",
        "Ի",
        "Ւ",
        "Ր",
        "ᣘ",
        "ᣗ",
        "ᣴ",
        "ᣚ",
        "𐓨",
        "𐓀",
        "𐓆",
        "𐓮",
    ],
    "s": ["ˢ", "ₛ", "⒮", "ⓢ", "ֆ", "Ֆ", "Ց", "ᣛ", "ᣵ", "ᙚ"],
    "t": ["ᵗ", "ₜ", "⒯", "ⓣ", "Ꮏ", "է", "ե", "Է", "Ե", "ᐪ", "ｔ"],
    "u": ["ᵘ", "ᵤ", "⒰", "ⓤ", "և", "ն", "մ", "Ա", "ע", "ᣕ", "𐓑"],
    "v": ["ᵛ", "ᵥ", "⒱", "ⓥ"],
    "w": ["ʷ", "⒲", "ⓦ", "ᐜ", "𐓑"],
    "x": ["ˣ", "ₓ", "⒳", "ⓧ"],
    "y": ["ʸ", "⒴", "ⓨ"],
    "z": ["ᶻ", "⒵", "ⓩ", "ᙇ", "ᙆ"],
    # \/ Upper case \/
    "A": [
        "ᴬ",
        "Ⓐ",
        "ⓐ",
        "Ꭿ",
        "ᗋ",
        "🇦",
        "🄰",
        "🅐",
        "ᗑ",
        "🅰",
        "𐒰",
        "𐒱",
        "𐒲",
        "𐒳",
        "𐓘",
        "𐓚",
        "𐓙",
        "𐓛",
    ],
    "B": [
        "ᴮ",
        "Ⓑ",
        "ⓑ",
        "Ᏸ",
        "ᵦ",
        "ᏼ",
        "🇧",
        "🄱",
        "🅑",
        "ᙖ",
        "ᙝ",
        "ᙞ",
        "ᙫ",
        "ᙟ",
        "ᙪ",
        "ᙩ",
        "ᙘ",
        "🅱",
    ],
    "C": [
        "ᶜ",
        "Ⓒ",
        "ⓒ",
        "Ꮹ",
        "Ꮳ",
        "Շ",
        "🇨",
        "🄫",
        "🄲",
        "🅒",
        "ᘳ",
        "ᑕ",
        "ᑖ",
        "ᑪ",
        "ᑡ",
        "ᑢ",
        "ᑣ",
        "ᑤ",
        "ᒼ",
        "ᑥ",
        "ᑦ",
        "ᔍ",
        "🅲",
    ],
    "D": ["ᴰ", "Ⓓ", "ⓓ", "🇩", "🄳", "🅓", "🅳", "𐓭", "𐓬", "𐓈", "𐓉", "𐓄", "𐓅"],
    "E": ["ᴱ", "Ⓔ", "ⓔ", "🇪", "🄴", "🅔", "ᙓ", "ᙦ", "ᣰ", "€", "🅴"],
    "F": ["ᶠ", "Ⓕ", "ⓕ", "🇫", "🄵", "🅕", "🅵"],
    "G": [
        "ᴳ",
        "Ⓖ",
        "ⓖ",
        "Ᏽ",
        "ᏻ",
        "ᏽ",
        "Ꮹ",
        "Ꮆ",
        "Շ",
        "🇬",
        "🄶",
        "🅖",
        "ᘳ",
        "ᘜ",
        "🅶",
        "𐒵",
        "𐒶",
        "𐓝",
        "𐓞",
    ],
    "H": ["ᴴ", "Ⓗ", "ⓗ", "🇭", "🄷", "🅗", "🅷"],
    "I": ["ᴵ", "Ⓘ", "ⓘ", "Ꮖ", "🇮", "🄸", "🅘", "🅸"],
    "J": ["ᴶ", "Ⓙ", "ⓙ", "ⱼ", "Ꮧ", "Ꮨ", "🇯", "🄹", "🅙", "🅹"],
    "K": ["ᴷ", "Ⓚ", "ⓚ", "🇰", "🄺", "🅚", "🅺", "𐒼", "𐒽", "𐒾", "𐓤", "𐓥", "𐓦"],
    "L": [
        "ᴸ",
        "Ⓛ",
        "ⓛ",
        "ւ",
        "լ",
        "ե",
        "Ն",
        "Լ",
        "Ը",
        "Ե",
        "🇱",
        "🄻",
        "🅛",
        "🅻",
        "𐓁",
        "𐓩",
    ],
    "M": ["ᴹ", "Ⓜ", "ⓜ", "🇲", "🄼", "🅜", "ᙨ", "ᔿ", "ᙢ", "🅼"],
    "N": ["ᴺ", "Ⓝ", "ⓝ", "𑪾", "𑪿", "🇳", "🄽", "🅝", "ᐢ", "🅽"],
    "O": ["ᴼ", "Ⓞ", "ⓞ", "Ꭴ", "Ꮎ", "֎", "֍", "🇴", "🄾", "🅞", "🅾"],
    "P": ["ᴾ", "Ⓟ", "ⓟ", "Ք", "🇵", "🄿", "🅟", "ᑮ", "ᑬ", "ᕶ", "ᕵ", "🅿", "🆊"],
    "Q": ["Ⓠ", "ⓠ", "🇶", "🅀", "🅠", "🆀"],
    "R": ["ᴿ", "Ⓡ", "ⓡ", "🇷", "🄬", "🅁", "🅡", "🆁", "🆊", "𐓜"],
    "S": ["ˢ", "Ⓢ", "ⓢ", "Ꭶ", "🇸", "🄪", "🅂", "🅢", "🆂"],
    "T": ["ᵀ", "Ⓣ", "ⓣ", "է", "Է", "🇹", "🅃", "🅣", "🆃", "𐓍"],
    "U": ["ᵁ", "Ⓤ", "ⓤ", "Ꮜ", "Մ", "🇺", "🅄", "ᐡ", "ᑘ", "ᑗ", "🅤", "ᘮ", "ᓑ", "🆄"],
    "V": ["ⱽ", "Ⓥ", "ⓥ", "Ꮴ", "Ꮙ", "🇻", "🅅", "ᐻ", "ᐺ", "🅥", "🆅"],
    "W": ["ᵂ", "Ⓦ", "ⓦ", "🇼", "🅆", "🅦", "ᙧ", "ᙡ", "🆆"],
    "X": ["ˣ", "Ⓧ", "ⓧ", "א", "🇽", "🅇", "🅧", "🆇"],
    "Y": ["ʸ", "Ⓨ", "ⓨ", "🇾", "🅈", "🅨", "🆈"],
    "Z": ["ᶻ", "Ⓩ", "ⓩ", "շ", "չ", "𑪼", "𑪽", "🇿", "🅉", "🅩", "🆉", "𐓓"],
    # \/ Numbers \/
    "0": ["⁰", "₀", "⓪", "Ꭴ", "Ꮎ", "🄀", "🄁", "🄋", "🄌"],
    "1": ["¹", "₁", "①", "🄂"],
    "2": ["²", "₂", "②", "ջ", "Չ", "Ձ", "Զ", "🄃"],
    "3": ["³", "₃", "③", "Յ", "🄄", "ᙣ", "ᙤ", "ᙥ"],
    "4": ["⁴", "₄", "④", "վ", "կ", "Վ", "Կ", "🄅"],
    "5": ["⁵", "₅", "⑤", "🄆"],
    "6": ["⁶", "₆", "⑥", "ճ", "Ճ", "🄇"],
    "7": ["⁷", "₇", "⑦", "🄈"],
    "8": ["⁸", "₈", "⑧", "🄉"],
    "9": ["⁹", "₉", "⑨", "Գ", "פּ", "ףּ", "פֿ", "🄊"],
}

# Parse the confusables data
for line in confusables_data.splitlines():
    if line.startswith("#") or not line.strip():
        continue
    parts = line.split(";")
    if len(parts) < 2:
        continue
    source_char = parts[0].strip()
    target_chars = parts[1].strip()
    source_char = chr(int(source_char, 16))
    target_chars = "".join(chr(int(t.strip(), 16)) for t in target_chars.split())
    if source_char in confusables_dict:
        confusables_dict[source_char].append(target_chars)
    if target_chars in confusables_dict:
        confusables_dict[target_chars].append(source_char)

# Merge custom dictionary
for char, variants in custom_dict.items():
    if char in confusables_dict:
        confusables_dict[char] = list(set(confusables_dict[char] + variants))
    else:
        confusables_dict[char] = variants

# Add combining diacritical marks and precomposed characters
for char in confusables_dict:
    confusables_dict[char] = list(
        set(confusables_dict[char] + add_combining_marks(char))
    )

# Remove empty lists
confusables_dict = {k: v for k, v in confusables_dict.items() if v}

# Save the dictionary to a JSON file
with open("confusables.json", "w", encoding="utf-8") as f:
    json.dump(confusables_dict, f, ensure_ascii=False, indent=4)

print("confusables.json file created successfully.")
