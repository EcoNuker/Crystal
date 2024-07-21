# WARNING. This document may contain sensitive regexes that include swearing and slurs. Read at your own risk.
import re2

seperators = "\s\-\*.,_\+=!`:#$%^&()1234567890"


class chars:
    def __init__(self):
        self.char_swaps = {
            "!": "!ǃⵑ！",
            "$": "$＄",
            "%": "%％",
            "&": "&ꝸ＆",
            "'": "'`´ʹʻʼʽʾˈˊˋ˴ʹ΄՚՝י׳ߴߵᑊᛌ᾽᾿`´῾‘’‛′‵ꞌ＇｀𖽑𖽒",
            "(": "(❨❲〔﴾（［",
            ")": ")❩❳〕﴿）］",
            "*": "*٭⁎∗＊𐌟",
            "+": "+᛭➕＋𐊛",
            ",": ",¸؍٫‚ꓹ，",
            "-": "-˗۔‐‑‒–⁃−➖Ⲻ﹘",
            ".": ".٠۰܁܂․ꓸ꘎．𐩐𝅭",
            "/": "/᜵⁁⁄∕╱⟋⧸Ⳇ⼃〳ノ㇓丿／𝈺",
            ":": ":ː˸։׃܃܄ःઃ᛬᠃᠉⁚∶ꓽ꞉︰：",
            ";": ";;；",
            "<": "<˂ᐸᚲ‹❮＜𝈶",
            "=": "=᐀⹀゠꓿＝",
            ">": ">˃ᐳ›❯＞𖼿𝈷",
            "?": "?ɁʔॽᎮꛫ？",
            "@": "@＠",
            "0": "0OoΟοσОоՕօסه٥ھہە۵߀०০੦૦ଠ୦௦ం౦ಂ೦ംഠ൦ං๐໐ဝ၀ჿዐᴏᴑℴⲞⲟⵔ〇ꓳꬽﮦﮧﮨﮩﮪﮫﮬﮭﻩﻪﻫﻬ０Ｏｏ𐊒𐊫𐐄𐐬𐓂𐓪𐔖𑓐𑢵𑣈𑣗𑣠𝐎𝐨𝑂𝑜𝑶𝒐𝒪𝓞𝓸𝔒𝔬𝕆𝕠𝕺𝖔𝖮𝗈𝗢𝗼𝘖𝘰𝙊𝙤𝙾𝚘𝚶𝛐𝛔𝛰𝜊𝜎𝜪𝝄𝝈𝝤𝝾𝞂𝞞𝞸𝞼𝟎𝟘𝟢𝟬𝟶𞸤𞹤𞺄🯰",
            "1": "11Iil|ıƖǀɩɪ˛ͺΙιІіӀӏ׀וןا١۱ߊᎥᛁιℐℑℓℹⅈⅠⅰⅼ∣⍳⏽Ⲓⵏꓲꙇꭵﺍﺎ１Ｉｉｌ￨𐊊𐌉𐌠𑣃𖼨𝐈𝐢𝐥𝐼𝑖𝑙𝑰𝒊𝒍𝒾𝓁𝓘𝓲𝓵𝔦𝔩𝕀𝕚𝕝𝕴𝖎𝖑𝖨𝗂𝗅𝗜𝗶𝗹𝘐𝘪𝘭𝙄𝙞𝙡𝙸𝚒𝚕𝚤𝚰𝛊𝛪𝜄𝜤𝜾𝝞𝝸𝞘𝞲𝟏𝟙𝟣𝟭𝟷𞣇𞸀𞺀🯱",
            "2": "2ƧϨᒿꙄꛯꝚ２𝟐𝟚𝟤𝟮𝟸🯲",
            "3": "3ƷȜЗӠⳌꝪꞫ３𑣊𖼻𝈆𝟑𝟛𝟥𝟯𝟹🯳",
            "4": "4Ꮞ４𑢯𝟒𝟜𝟦𝟰𝟺🯴",
            "5": "5Ƽ５𑢻𝟓𝟝𝟧𝟱𝟻🯵",
            "6": "6бᏮⳒ６𑣕𝟔𝟞𝟨𝟲𝟼🯶",
            "7": "7７𐓒𑣆𝈒𝟕𝟟𝟩𝟳𝟽🯷",
            "8": "8Ȣȣ৪੪ଃ８𐌚𝟖𝟠𝟪𝟴𝟾𞣋🯸",
            "9": "9৭੧୨൭ⳊꝮ９𑢬𑣌𑣖𝟗𝟡𝟫𝟵𝟿🯹",
            "a": "a4ÁáÀàĂăẮắẰằẴẵẲẳÂâẤấẦầẪẫẨẩǍǎÅåǺǻÄäǞǟÃãȦȧǠǡĄąĄ́ą́Ą̃ą̃ĀāĀ̀ā̀ẢảȀȁA̋a̋ȂȃẠạẶặẬậḀḁȺⱥꞺꞻᶏẚＡ@ａ!",
            "e": "e3ÉéÈèĔĕẾếỀềỄễỂểÊêẾếỀềỄễỂểĚěËëĖėẸẹỆệȨȩĘęĒēĘ̃ę̃ḔḕỂẻỄẽȄȅE̋e̋ȆȇḘḙḚḛḜḝẸ̣ẼẽＥｅ3",
            "i": "il1ÍíÌìĬĭÎîĨĩÏïḮḯĮįĪīĪ̀ī̀ỊịȈȉI̋i̋ȊȋỈỉĬ̀ĭÌìÎ́íḬḭĨĩＩ!ｉ|",
            "o": "o0ÓóÒòŎŏÔôỐốỒồỖỗỔổǑǒÖöȪȫŐőÕõṌṍṎṏȬȭȮȯȰȱØøǾǿǪǫǬǭŌōȌȍȎȏỌọỘộƠơỚớỜờỠỡỞởỢợỤụṲṳṴṵṶṷṸṹṺṻỌ̣ÕõＯｏロ",
            "u": "uÚúÙùŬŭÛûŨũÜüǛǜǗǘǙǚǕǖŮůŰűŲųŪūỦủȔȕŰűȖȗỤụỨứỪừỮữỬửỰựṲṳṴṵṶṷṸṹṺṻṼṽṾṿŨũＵｕ",
            "b": "bBḂḃḄḅḆḇɃƀƁɓƂƃʙʙＢｂ",
            "c": "cCĆćĈĉĊċČčÇçḈḉȻȼƇƈɕÇ̃ç̃ＣｃkKĶķĸḰḱǨǩḲḳḴḵƘƙꝀꝁⱩⱪꝂꝃꝄꝅＫｋ",
            "d": "dDĎďḊḋḌḍḐḑḒḓĐđƉƊƋƌɖɗＤｄ",
            "f": "fFḞḟƑƒꞘꞙＦｆ!",
            "g": "gGĜĝĞğĠġĢģǤǥǦǧǴǵḠḡƓɠＧｇ",
            "h": "hHĤĥȞȟḢḣḤḥḦḧḨḩḪḫẖĦħⱧⱨꞪꞫＨｈ",
            "j": "jJĴĵɈɉǰȷɟʄＪｊ!",
            "k": "kKĶķĸḰḱǨǩḲḳḴḵƘƙꝀꝁⱩⱪꝂꝃꝄꝅＫｋcCĆćĈĉĊċČčÇçḈḉȻȼƇƈɕÇ̃ç̃Ｃｃ",
            "l": "liLĹĺĻļĽľĿŀŁłḶḷḸḹḺḻḼḽȽⱠⱡⱢɫꞀꞁＬｌ|!",
            "m": "mMḾḿṀṁṂṃⱮɱＭｍ",
            "n": "nNŃńŅņŇňÑñṄṅṆṇṈṉṊṋƝɲȠƞＮ𝓃ｎ",
            "p": "pPṔṕṖṗⱣƤƥＰｐ",
            "q": "qQɊɋＱｑ8Ȣȣ৪੪ଃ８𐌚𝟖𝟠𝟪𝟴𝟾𞣋🯸",
            "r": "r𝓇RŔŕŖŗŘřȐȑȒȓṘṙṚṛṜṝṞṟɌɍⱤɽＲｒ",
            "s": "sSŚśŜŝŞşŠšȘșṠṡṢṣṤṥṦṧṨṩẛẞßⱾꞨꞩzZŹźŻżŽžẐẑẒẓẔẕƵƶȤȥⱫⱬꝢꝣＺｚ",
            "t": "𝓉tTŢţŤťṪṫȚțṬṭṮṯṰṱŦŧƬƭƮȚʈＴｔ",
            "v": "vVṼṽṾṿƲʋꝞꝟＶｖ",
            "w": "wWẀẁẂẃŴŵẆẇẈẉẘⱲⱳＷｗ",
            "x": "xXẊẋẌẍＸｘ",
            "y": "yYÝýỲỳŶŷŸÿȲȳẎẏỴỵƳƴỶỷỾỿɎɏＹｙ",
            "z": "zZŹźŻżŽžẐẑẒẓẔẕƵƶȤȥⱫⱬꝢꝣＺｚsSŚśŜŝŞşŠšȘșṠṡṢṣṤṥṦṧṨṩẛẞßⱾꞨꞩ",
        }
        self.additional = {
            "A": "AΑАᎪᗅᴀꓮꭺＡ𐊠𖽀𝐀𝐴𝑨𝒜𝓐𝔄𝔸𝕬𝖠𝗔𝘈𝘼𝙰𝚨𝛢𝜜𝝖𝞐",
            "B": "BʙΒВвᏴᏼᗷᛒℬꓐꞴＢ𐊂𐊡𐌁𝐁𝐵𝑩𝓑𝔅𝔹𝕭𝖡𝗕𝘉𝘽𝙱𝚩𝛣𝜝𝝗𝞑",
            "C": "CϹСᏟᑕℂℭⅭ⊂Ⲥ⸦ꓚＣ𐊢𐌂𐐕𐔜𑣩𑣲𝐂𝐶𝑪𝒞𝓒𝕮𝖢𝗖𝘊𝘾𝙲🝌匚",
            "D": "DᎠᗞᗪᴅⅅⅮꓓꭰＤ𝐃𝐷𝑫𝒟𝓓𝔇𝔻𝕯𝖣𝗗𝘋𝘿𝙳",
            "E": "EΕЕᎬᴇℰ⋿ⴹꓰꭼＥ𐊆𑢦𑢮𝐄𝐸𝑬𝓔𝔈𝔼𝕰𝖤𝗘𝘌𝙀𝙴𝚬𝛦𝜠𝝚𝞔",
            "F": "FϜᖴℱꓝꞘＦ𐊇𐊥𐔥𑢢𑣂𝈓𝐅𝐹𝑭𝓕𝔉𝔽𝕱𝖥𝗙𝘍𝙁𝙵𝟊",
            "G": "GɢԌԍᏀᏳᏻꓖꮐＧ𝐆𝐺𝑮𝒢𝓖𝔊𝔾𝕲𝖦𝗚𝘎𝙂𝙶",
            "H": "HʜΗНнᎻᕼℋℌℍⲎꓧꮋＨ𐋏𝐇𝐻𝑯𝓗𝕳𝖧𝗛𝘏𝙃𝙷𝚮𝛨𝜢𝝜𝞖",
            "J": "JͿЈᎫᒍᴊꓙꞲꭻＪ𝐉𝐽𝑱𝒥𝓙𝔍𝕁𝕵𝖩𝗝𝘑𝙅𝙹",
            "K": "KΚКᏦᛕKⲔꓗＫ𐔘𝐊𝐾𝑲𝒦𝓚𝔎𝕂𝕶𝖪𝗞𝘒𝙆𝙺𝚱𝛫𝜥𝝟𝞙",
            "L": "LʟᏞᒪℒⅬⳐⳑꓡꮮＬ𐐛𐑃𐔦𑢣𑢲𖼖𝈪𝐋𝐿𝑳𝓛𝔏𝕃𝕷𝖫𝗟𝘓𝙇𝙻",
            "M": "MΜϺМᎷᗰᛖℳⅯⲘꓟＭ𐊰𐌑𝐌𝑀𝑴𝓜𝔐𝕄𝕸𝖬𝗠𝘔𝙈𝙼𝚳𝛭𝜧𝝡𝞛",
            "N": "NɴΝℕⲚꓠＮ𐔓𝐍𝑁𝑵𝒩𝓝𝔑𝕹𝖭𝗡𝘕𝙉𝙽𝚴𝛮𝜨𝝢𝞜",
            "P": "PΡРᏢᑭᴘᴩℙⲢꓑꮲＰ𐊕𝐏𝑃𝑷𝒫𝓟𝔓𝕻𝖯𝗣𝘗𝙋𝙿𝚸𝛲𝜬𝝦𝞠",
            "Q": "QℚⵕＱ𝐐𝑄𝑸𝒬𝓠𝔔𝕼𝖰𝗤𝘘𝙌𝚀",
            "R": "RƦʀᎡᏒᖇᚱℛℜℝꓣꭱꮢＲ𐒴𖼵𝈖𝐑𝑅𝑹𝓡𝕽𝖱𝗥𝘙𝙍𝚁尺",
            "S": "SЅՏᏕᏚꓢＳ𐊖𐐠𖼺𝐒𝑆𝑺𝒮𝓢𝔖𝕊𝕾𝖲𝗦𝘚𝙎𝚂",
            "T": "TΤτТтᎢᴛ⊤⟙ⲦꓔꭲＴ𐊗𐊱𐌕𑢼𖼊𝐓𝑇𝑻𝒯𝓣𝔗𝕋𝕿𝖳𝗧𝘛𝙏𝚃𝚻𝛕𝛵𝜏𝜯𝝉𝝩𝞃𝞣𝞽🝨丅",
            "U": "UՍሀᑌ∪⋃ꓴＵ𐓎𑢸𖽂𝐔𝑈𝑼𝒰𝓤𝔘𝕌𝖀𝖴𝗨𝘜𝙐𝚄凵",
            "V": "VѴ٧۷ᏙᐯⅤⴸꓦꛟＶ𐔝𑢠𖼈𝈍𝐕𝑉𝑽𝒱𝓥𝔙𝕍𝖁𝖵𝗩𝘝𝙑𝚅",
            "W": "WԜᎳᏔꓪＷ𑣦𑣯𝐖𝑊𝑾𝒲𝓦𝔚𝕎𝖂𝖶𝗪𝘞𝙒𝚆",
            "X": "XΧХ᙭ᚷⅩ╳ⲬⵝꓫꞳＸ𐊐𐊴𐌗𐌢𐔧𑣬𝐗𝑋𝑿𝒳𝓧𝔛𝕏𝖃𝖷𝗫𝘟𝙓𝚇𝚾𝛸𝜲𝝬𝞦",
            "Y": "YΥϒУҮᎩᎽⲨꓬＹ𐊲𑢤𖽃𝐘𝑌𝒀𝒴𝓨𝔜𝕐𝖄𝖸𝗬𝘠𝙔𝚈𝚼𝛶𝜰𝝪𝞤",
            "Z": "ZΖᏃℤℨꓜＺ𐋵𑢩𑣥𝐙𝑍𝒁𝒵𝓩𝖅𝖹𝗭𝘡𝙕𝚉𝚭𝛧𝜡𝝛𝞕",
            "a": "aɑαа⍺ａ𝐚𝑎𝒂𝒶𝓪𝔞𝕒𝖆𝖺𝗮𝘢𝙖𝚊𝛂𝜶𝝰𝞪",
            "b": "bԌЬᏏᖯｂ𝐛𝑏𝒃𝒷𝓫𝔟𝕓𝖇𝖻𝗯𝘣𝙗𝚋",
            "c": "cϲсⲥｃ𑣠𑣩𝐜𝑐𝒄𝓬𝔠𝕔𝖈𝖼𝗰𝘤𝙘𝚌",
            "d": "dԀժᏧｄ𝐝𝑑𝒅𝒹𝓭𝔡𝕕𝖉𝖽𝗱𝘥𝙙𝚍",
            "e": "eеҽ℮ℯｅ𑢦𝐞𝑒𝒆𝒶𝓮𝔢𝕖𝖊𝖾𝗲𝘦𝙚𝚎",
            "f": "fϝғꬵｆ𐔯𝐟𝑓𝒇𝒻𝓯𝔣𝕗𝖋𝗳𝘧𝙛𝚏",
            "g": "gɡցᶃℊｇ𝐠𝑔𝒈𝓰𝔤𝕘𝖌𝗀𝗴𝘨𝙜𝚐",
            "h": "hһⲏｈ𐔥𝐡𝒉𝒽𝓱𝔥𝕙𝖍𝗁𝗵𝘩𝙝𝚑",
            "i": "iıɪιіاᎥᛁｉ𑣃𝐢𝑖𝒊𝒾𝓲𝔦𝕚𝖎𝗂𝗶𝘪𝙞𝚒𝛊𝜄𝝸𝞲工",
            "j": "jϳјյｊ𝐣𝑗𝒋𝓳𝔧𝕛𝖏𝗃𝗷𝘫𝙟𝚓",
            "k": "kκкⲕｋ𑣘𖽑𝐤𝑘𝒌𝓀𝓴𝔨𝕜𝖐𝗄𝗸𝘬𝙠𝚔",
            "l": "lɩΙІⅼ∣ⵏⵑꓲｌ𑣐𝐥𝑙𝒍𝓁𝓵𝔩𝕝𝖑𝗅𝗹𝘭𝙡𝚕",
            "m": "mｍ𑣃𖼵𝐦𝑚𝒎𝓂𝓶𝔪𝕞𝖒𝗆𝗺𝘮𝙢𝚖",
            "n": "nոⲛⵏꓠꮴｎ𝐧𝑛𝒏𝓃𝓷𝔫𝕟𝖓𝗇𝗻𝘯𝙣𝚗",
            "o": "oοоⲟⵔｏ𝐨𝑜𝒐𝒾𝓸𝔬𝕠𝖔𝗈𝗼𝘰𝙤𝚘口",
            "p": "pρрⲣｐ𝐩𝑝𝒑𝓅𝓹𝔭𝕡𝖕𝗉𝗽𝘱𝙥𝚙",
            "q": "qԛզｑ𝐪𝑞𝒒𝓆𝓺𝔮𝕢𝖖𝗊𝗾𝘲𝙦𝚚",
            "w": "w山",
        }
        self.leetspeak = {
            "a": "4Ꮞ４𑢯𝟒𝟜𝟦𝟰𝟺🯴",
            "b": "6бᏮⳒ６𑣕𝟔𝟞𝟨𝟲𝟼🯶8Ȣȣ৪੪ଃ８𐌚𝟖𝟠𝟪𝟴𝟾𞣋🯸",
            "q": "9৭੧୨൭ⳊꝮ９𑢬𑣌𑣖𝟗𝟡𝟫𝟵𝟿🯹",
            "e": "3ƷȜЗӠⳌꝪꞫ３𑣊𖼻𝈆𝟑𝟛𝟥𝟯𝟹🯳",
            "g": "6бᏮⳒ６𑣕𝟔𝟞𝟨𝟲𝟼🯶8Ȣȣ৪੪ଃ８𐌚𝟖𝟠𝟪𝟴𝟾𞣋🯸9৭੧୨൭ⳊꝮ９𑢬𑣌𑣖𝟗𝟡𝟫𝟵𝟿🯹",
            "t": "7７𐓒𑣆𝈒𝟕𝟟𝟩𝟳𝟽🯷",
            "l": "7７𐓒𑣆𝈒𝟕𝟟𝟩𝟳𝟽🯷",
            "y": "7７𐓒𑣆𝈒𝟕𝟟𝟩𝟳𝟽🯷",
            "o": "0OoΟοσОоՕօסه٥ھہە۵߀०০੦૦ଠ୦௦ం౦ಂ೦ംഠ൦ං๐໐ဝ၀ჿዐᴏᴑℴⲞⲟⵔ〇ꓳꬽﮦﮧﮨﮩﮪﮫﮬﮭﻩﻪﻫﻬ０Ｏｏ𐊒𐊫𐐄𐐬𐓂𐓪𐔖𑓐𑢵𑣈𑣗𑣠𝐎𝐨𝑂𝑜𝑶𝒐𝒪𝓞𝓸𝔒𝔬𝕆𝕠𝕺𝖔𝖮𝗈𝗢𝗼𝘖𝘰𝙊𝙤𝙾𝚘𝚶𝛐𝛔𝛰𝜊𝜎𝜪𝝄𝝈𝝤𝝾𝞂𝞞𝞸𝞼𝟎𝟘𝟢𝟬𝟶𞸤𞹤𞺄🯰",
            "l": "11Iil|ıƖǀɩɪ˛ͺΙιІіӀӏ׀וןا١۱ߊᎥᛁιℐℑℓℹⅈⅠⅰⅼ∣⍳⏽Ⲓⵏꓲꙇꭵﺍﺎ１Ｉｉｌ￨𐊊𐌉𐌠𑣃𖼨𝐈𝐢𝐥𝐼𝑖𝑙𝑰𝒊𝒍𝒾𝓁𝓘𝓲𝓵𝔦𝔩𝕀𝕚𝕝𝕴𝖎𝖑𝖨𝗂𝗅𝗜𝗶𝗹𝘐𝘪𝘭𝙄𝙞𝙡𝙸𝚒𝚕𝚤𝚰𝛊𝛪𝜄𝜤𝜾𝝞𝝸𝞘𝞲𝟏𝟙𝟣𝟭𝟷𞣇𞸀𞺀🯱",
            "i": "11Iil|ıƖǀɩɪ˛ͺΙιІіӀӏ׀וןا١۱ߊᎥᛁιℐℑℓℹⅈⅠⅰⅼ∣⍳⏽Ⲓⵏꓲꙇꭵﺍﺎ１Ｉｉｌ￨𐊊𐌉𐌠𑣃𖼨𝐈𝐢𝐥𝐼𝑖𝑙𝑰𝒊𝒍𝒾𝓁𝓘𝓲𝓵𝔦𝔩𝕀𝕚𝕝𝕴𝖎𝖑𝖨𝗂𝗅𝗜𝗶𝗹𝘐𝘪𝘭𝙄𝙞𝙡𝙸𝚒𝚕𝚤𝚰𝛊𝛪𝜄𝜤𝜾𝝞𝝸𝞘𝞲𝟏𝟙𝟣𝟭𝟷𞣇𞸀𞺀🯱",
            "s": "5Ƽ５𑢻𝟓𝟝𝟧𝟱𝟻🯵",
            "z": "2ƧϨᒿꙄꛯꝚ２𝟐𝟚𝟤𝟮𝟸🯲",
        }

        for key, values in self.additional.items():
            key = key.lower()
            self.char_swaps[key] = "".join(
                list(set([*(self.char_swaps.get(key, "") + values)]))
            )

    def get_char(self, c: str, include_leetspeak: bool = False):
        char_swaps = self.char_swaps.copy()
        leetspeak = self.char_swaps.copy()
        if include_leetspeak:
            for key, values in leetspeak.items():
                key = key.lower()
                char_swaps[key] = "".join(
                    list(set([*(char_swaps.get(key, "") + values)]))
                )
        return "".join(list(set([*c + char_swaps.get(c.lower(), "")])))


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

    return regex


slurs = [
    allow_seperators(
        f"\\b(?i)([{CHARS.get_char('s', include_leetspeak=True)}][{CHARS.get_char('a', include_leetspeak=True)}][{CHARS.get_char('n', include_leetspeak=True)}][{CHARS.get_char('d', include_leetspeak=True)}])*[{CHARS.get_char('n', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}{CHARS.get_char('o', include_leetspeak=True)}{CHARS.get_char('a', include_leetspeak=True)}]*[{CHARS.get_char('g', include_leetspeak=True)}]+[{CHARS.get_char('g', include_leetspeak=True)}]+(l[{CHARS.get_char('e', include_leetspeak=True)}]+t+|[{CHARS.get_char('e', include_leetspeak=True)}{CHARS.get_char('a', include_leetspeak=True)}]*[{CHARS.get_char('r', include_leetspeak=True)}]*|n[{CHARS.get_char('o', include_leetspeak=True)}]+[{CHARS.get_char('g', include_leetspeak=True)}]+|[{CHARS.get_char('a', include_leetspeak=True)}]*)*[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}{CHARS.get_char('h', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('n', include_leetspeak=True)}]+([{CHARS.get_char('e', include_leetspeak=True)}]|[{CHARS.get_char('i', include_leetspeak=True)}])+[{CHARS.get_char('g', include_leetspeak=True)}]+(([{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('o', include_leetspeak=True)}]+)|([{CHARS.get_char('l', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+[{CHARS.get_char('t', include_leetspeak=True)}]+))[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('t', include_leetspeak=True)}]+[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('a', include_leetspeak=True)}]+[{CHARS.get_char('n', include_leetspeak=True)}]+([{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+|[{CHARS.get_char('y', include_leetspeak=True)}]+|[{CHARS.get_char('e', include_leetspeak=True)}]+[{CHARS.get_char('r', include_leetspeak=True)}]+)[{CHARS.get_char('z', include_leetspeak=True)}{CHARS.get_char('s', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('f', include_leetspeak=True)}]+[{CHARS.get_char('a', include_leetspeak=True)}]+[{CHARS.get_char('g', include_leetspeak=True)}]+([{CHARS.get_char('g', include_leetspeak=True)}{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('t', include_leetspeak=True)}]+([{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('y', include_leetspeak=True)}]+|[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+)?|([{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}])?)?([{CHARS.get_char('s', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+)?[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('k', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('k', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]([{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('y', include_leetspeak=True)}]+|[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]+)?[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('c', include_leetspeak=True)}]+[{CHARS.get_char('h', include_leetspeak=True)}]+[{CHARS.get_char('i', include_leetspeak=True)}]+[{CHARS.get_char('n', include_leetspeak=True)}]+[{CHARS.get_char('k', include_leetspeak=True)}]+[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
    allow_seperators(
        f"\\b(?i)[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('e', include_leetspeak=True)}]*[{CHARS.get_char('t', include_leetspeak=True)}]+[{CHARS.get_char('a', include_leetspeak=True)}]+[{CHARS.get_char('r', include_leetspeak=True)}]+[{CHARS.get_char('d', include_leetspeak=True)}]+([{CHARS.get_char('e', include_leetspeak=True)}]+[{CHARS.get_char('d', include_leetspeak=True)}]+)?[{CHARS.get_char('s', include_leetspeak=True)}{CHARS.get_char('z', include_leetspeak=True)}]*\\b"
    ),
]

# slurs LIST IN ORDER:
# nigger/nigga + pluralized (double g mandatory to match)
# negro/niglet + pluralized
# tranny + pluralized (double n NOT mandatory to match)
# faggot + faggie (double g NOT mandatory)
# kike
# chink
# retard/rtard/retarded + pluralized

invites = [
    r"(?i)(?:https?:\/\/)?(?:www.|ptb.|canary.)?(?:dsc\.gg|invite\.gg|discord\.link|(?:discord\.(?:gg|io|me|li|id))|disboard\.org|discord(?:app)?\.(?:com|gg)\/(?:invite|servers))\/[a-z0-9-_]+",
    r"(?i)(?:https?:\/\/)?(?:www\.)?(?:guilded\.(?:gg|com))\/(?:i\/[a-z0-9-_]+|[a-z0-9-_]+)",
    r"(?i)(?:https?:\/\/)?(?:www\.)?(?:revolt\.chat|rvlt\.gg)(?:\/[a-zA-Z0-9_-]+)*",
]

invites_exclusions = {
    "guilded": ["TheGG", "Guilded-Official", "EcoNuker", "API-Official"],
    "discord": [],
    "revolt": ["posts", "tracker"],
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
fart
fartknocker
fat
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
