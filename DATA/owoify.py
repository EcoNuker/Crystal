import collections.abc, random, re


def owoify(source: str, level: int = 0, symbols: bool = True) -> str:
    """
    Pass the source string and the desired level of owoness to owoify it.
    ----
    Inputs:
    - source (str) : The source string
    - level (int) : How much it should be owoified. 0-2, 0 being low and 2 being high
    - symbols (bool) : Whether to replace symbols (such as `"<", ">", "[", "]", "{", "}", ".", ",", ";", "!"`)
    ----
    Outputs:
    - str : The owoified string.
    ----
    Raises:
    - RuntimeError : Level is not supported
    """
    WORD_REGEX = re.compile(r"[^\s]+")
    SPACE_REGEX = re.compile(r"\s+")
    word_matches = WORD_REGEX.findall(source)
    space_matches = SPACE_REGEX.findall(source)

    def flatten(arr: collections.abc.Iterable):
        """
        Flatten the iterable collection. Modified from: https://note.nkmk.me/en/python-list-flatten/
        :param arr: The iterable collection to flatten
        :return: The generator of the flattened collection.
        """
        for elem in arr:
            if isinstance(elem, collections.abc.Iterable) and not isinstance(
                elem, (str, bytes)
            ):
                yield from flatten(elem)
            else:
                yield elem

    class Word:
        def __init__(self, word: str):
            self.replaced_words: set = set()
            self.word = word

        def __str__(self) -> str:
            return self.word

        def selector(
            self, s: str, search_value: re.Pattern, replace_value: str
        ) -> bool:
            if search_value.search(s) is not None:
                match_result = search_value.search(s).group()
                return s.replace(match_result, replace_value) == replace_value
            return False

        def search_value_contains_replaced_words(
            self, search_value: re.Pattern, replace_value: str
        ) -> bool:
            return any(
                self.selector(s, search_value, replace_value)
                for s in self.replaced_words
            )

        def replace(
            self,
            search_value: re.Pattern,
            replace_value: str,
            replace_replaced_words: bool = False,
        ):
            if (
                not replace_replaced_words
                and self.search_value_contains_replaced_words(
                    search_value, replace_value
                )
            ):
                return self
            replacing_word = self.word
            if search_value.search(self.word) is not None:
                replacing_word = search_value.sub(replace_value, self.word)
            collection = search_value.findall(self.word)
            if len(collection) > 1:
                replaced_words = list(
                    map(lambda s: s.replace(s, replace_value), collection)
                )
            else:
                replaced_words = []

            if replacing_word != self.word:
                for word in replaced_words:
                    self.replaced_words.add(word)
                self.word = replacing_word
            return self

        def replace_with_func_single(
            self, search_value: re.Pattern, func, replace_replaced_words: bool = False
        ):
            replace_value = func()
            if (
                not replace_replaced_words
                and self.search_value_contains_replaced_words(
                    search_value, replace_value
                )
            ):
                return self
            replacing_word = self.word
            if search_value.search(self.word) is not None:
                match = search_value.search(self.word).group()
                replacing_word = self.word.replace(match, replace_value)
            collection = search_value.findall(self.word)
            if len(collection) > 1:
                replaced_words = list(
                    map(lambda s: s.replace(s, replace_value), collection)
                )
            else:
                replaced_words = []
            if replacing_word != self.word:
                for word in replaced_words:
                    self.replaced_words.add(word)
                self.word = replacing_word
            return self

        def replace_with_func_multiple(
            self, search_value: re.Pattern, func, replace_replaced_words: bool = False
        ):
            if search_value.search(self.word) is None:
                return self
            word = self.word
            captures = search_value.search(word)
            replace_value = func(captures.group(1), captures.group(2))
            if (
                not replace_replaced_words
                and self.search_value_contains_replaced_words(
                    search_value, replace_value
                )
            ):
                return self
            replacing_word = self.word.replace(captures.group(0), replace_value)
            collection = search_value.findall(self.word)
            collection = list(flatten(collection))
            if len(collection) > 1:
                replaced_words = list(
                    map(lambda s: s.replace(s, replace_value), collection)
                )
            else:
                replaced_words = []
            if replacing_word != self.word:
                for word in replaced_words:
                    self.replaced_words.add(word)
                self.word = replacing_word
            return self

    O_TO_OWO = re.compile(r"o")
    EW_TO_UWU = re.compile(r"ew")
    HEY_TO_HAY = re.compile(r"([Hh])ey")
    DEAD_TO_DED_UPPER = re.compile(r"Dead")
    DEAD_TO_DED_LOWER = re.compile(r"dead")
    N_VOWEL_T_TO_ND = re.compile(r"n[aeiou]*t")
    READ_TO_WEAD_UPPER = re.compile(r"Read")
    READ_TO_WEAD_LOWER = re.compile(r"read")
    BRACKETS_TO_STARTRAILS_FORE = re.compile(r"[({<]")
    BRACKETS_TO_STARTRAILS_REAR = re.compile(r"[)}>]")
    PERIOD_COMMA_EXCLAMATION_SEMICOLON_TO_KAOMOJIS_FIRST = re.compile(r"[.,](?![0-9])")
    PERIOD_COMMA_EXCLAMATION_SEMICOLON_TO_KAOMOJIS_SECOND = re.compile(r"[!;]+")
    THAT_TO_DAT_UPPER = re.compile(r"That")
    THAT_TO_DAT_LOWER = re.compile(r"that")
    TH_TO_F_UPPER = re.compile(r"TH(?!E)")
    TH_TO_F_LOWER = re.compile(r"[Tt]h(?![Ee])")
    LE_TO_WAL = re.compile(r"le$")
    VE_TO_WE_UPPER = re.compile(r"Ve")
    VE_TO_WE_LOWER = re.compile(r"ve")
    RY_TO_WWY = re.compile(r"ry")
    RORL_TO_W_UPPER = re.compile(r"(?:R|L)")
    RORL_TO_W_LOWER = re.compile(r"(?:r|l)")
    LL_TO_WW = re.compile(r"ll")
    VOWEL_OR_R_EXCEPT_O_L_TO_WL_UPPER = re.compile(r"[AEIUR]([lL])$")
    VOWEL_OR_R_EXCEPT_O_L_TO_WL_LOWER = re.compile(r"[aeiur]l$")
    OLD_TO_OWLD_UPPER = re.compile(r"OLD")
    OLD_TO_OWLD_LOWER = re.compile(r"([Oo])ld")
    OL_TO_OWL_UPPER = re.compile(r"OL")
    OL_TO_OWL_LOWER = re.compile(r"([Oo])l")
    LORR_O_TO_WO_UPPER = re.compile(r"[LR]([oO])")
    LORR_O_TO_WO_LOWER = re.compile(r"[lr]o")
    SPECIFIC_CONSONANTS_O_TO_LETTER_AND_WO_UPPER = re.compile(
        r"([BCDFGHJKMNPQSTXYZ])([oO])"
    )
    SPECIFIC_CONSONANTS_O_TO_LETTER_AND_WO_LOWER = re.compile(r"([bcdfghjkmnpqstxyz])o")
    VORW_LE_TO_WAL = re.compile(r"[vw]le")
    FI_TO_FWI_UPPER = re.compile(r"FI")
    FI_TO_FWI_LOWER = re.compile(r"([Ff])i")
    VER_TO_WER = re.compile(r"([Vv])er")
    POI_TO_PWOI = re.compile(r"([Pp])oi")
    SPECIFIC_CONSONANTS_LE_TO_LETTER_AND_WAL = re.compile(
        r"([DdFfGgHhJjPpQqRrSsTtXxYyZz])le$"
    )
    CONSONANT_R_TO_CONSONANT_W = re.compile(r"([BbCcDdFfGgKkPpQqSsTtWwXxZz])r")
    LY_TO_WY_UPPER = re.compile(r"Ly")
    LY_TO_WY_LOWER = re.compile(r"ly")
    PLE_TO_PWE = re.compile(r"([Pp])le")
    NR_TO_NW_UPPER = re.compile(r"NR")
    NR_TO_NW_LOWER = re.compile(r"([Nn])r")
    MEM_TO_MWEM_UPPER = re.compile(r"Mem")
    MEM_TO_MWEM_LOWER = re.compile(r"mem")
    NYWO_TO_NYO = re.compile(r"([Nn])ywo")
    FUC_TO_FWUC = re.compile(r"([Ff])uc")
    MOM_TO_MWOM = re.compile(r"([Mm])om")
    ME_TO_MWE_UPPER = re.compile(r"^Me$")
    ME_TO_MWE_LOWER = re.compile(r"^me$")
    N_VOWEL_TO_NY_FIRST = re.compile(r"n([aeiou])")
    N_VOWEL_TO_NY_SECOND = re.compile(r"N([aeiou])")
    N_VOWEL_TO_NY_THIRD = re.compile(r"N([AEIOU])")
    OVE_TO_UV_UPPER = re.compile(r"OVE")
    OVE_TO_UV_LOWER = re.compile(r"ove")
    HAHA_TO_HEHE_XD = re.compile(r"\b(ha|hah|heh|hehe)+\b")
    THE_TO_TEH = re.compile(r"\b([Tt])he\b")
    YOU_TO_U_UPPER = re.compile(r"\bYou\b")
    YOU_TO_U_LOWER = re.compile(r"\byou\b")
    TIME_TO_TIM = re.compile(r"\b([Tt])ime\b")
    OVER_TO_OWOR = re.compile(r"([Oo])ver")
    WORSE_TO_WOSE = re.compile(r"([Ww])orse")
    GREAT_TO_GWATE = re.compile(r"([Gg])reat")
    AVIAT_TO_AWIAT = re.compile(r"([Aa])viat")
    DEDICAT_TO_DEDITAT = re.compile(r"([Dd])edicat")
    REMEMBER_TO_REMBER = re.compile(r"([Rr])emember")
    WHEN_TO_WEN = re.compile(r"([Ww])hen")
    FRIGHTENED_TO_FRIGTEN = re.compile(r"([Ff])righten(ed)*")
    MEME_TO_MEM_FIRST = re.compile(r"Meme")
    MEME_TO_MEM_SECOND = re.compile(r"Mem")
    FEEL_TO_FELL = re.compile(r"^([Ff])eel$")

    # Additional kaomojis come from [owoify](https://pypi.org/project/owoify/) and Discord.
    FACES = [
        "(・`ω´・)",
        ";;w;;",
        "owo",
        "UwU",
        ">w<",
        "^w^",
        "(* ^ ω ^)",
        "(⌒ω⌒)",
        "ヽ(*・ω・)ﾉ",
        "(o´∀`o)",
        "(o･ω･o)",
        "＼(＾▽＾)／",
        "(*^ω^)",
        "(◕‿◕✿)",
        "(◕ᴥ◕)",
        "ʕ•ᴥ•ʔ",
        "ʕ￫ᴥ￩ʔ",
        "(*^.^*)",
        "(｡♥‿♥｡)",
        "OwO",
        "uwu",
        "uvu",
        "UvU",
        "(*￣з￣)",
        "(つ✧ω✧)つ",
        "(/ =ω=)/",
        "(╯°□°）╯︵ ┻━┻",
        "┬─┬ ノ( ゜-゜ノ)",
        "¯\\_(ツ)_/¯",
    ]

    def map_o_to_owo(input: Word) -> Word:
        replacement: str
        if random.randint(0, 2) > 0:
            replacement = "owo"
        else:
            replacement = "o"
        return input.replace(O_TO_OWO, replacement)

    def map_ew_to_uwu(input: Word) -> Word:
        return input.replace(EW_TO_UWU, "uwu")

    def map_hey_to_hay(input: Word) -> Word:
        return input.replace(HEY_TO_HAY, "\\1ay")

    def map_dead_to_ded(input: Word) -> Word:
        return input.replace(DEAD_TO_DED_UPPER, "Ded").replace(DEAD_TO_DED_LOWER, "ded")

    def map_n_vowel_t_to_nd(input: Word) -> Word:
        return input.replace(N_VOWEL_T_TO_ND, "nd")

    def map_read_to_wead(input: Word) -> Word:
        return input.replace(READ_TO_WEAD_UPPER, "Wead").replace(
            READ_TO_WEAD_LOWER, "wead"
        )

    def map_brackets_to_star_trails(input: Word) -> Word:
        if symbols:
            return input.replace(
                BRACKETS_TO_STARTRAILS_FORE, "｡･:*:･ﾟ★,｡･:*:･ﾟ☆"
            ).replace(BRACKETS_TO_STARTRAILS_REAR, "☆ﾟ･:*:･｡,★ﾟ･:*:･｡")
        return input

    def map_period_comma_exclamation_semicolon_to_kaomojis(input: Word) -> Word:
        if symbols:
            return input.replace_with_func_single(
                PERIOD_COMMA_EXCLAMATION_SEMICOLON_TO_KAOMOJIS_FIRST,
                lambda: f" {FACES[random.randint(0, len(FACES) - 1)]}",
            ).replace_with_func_single(
                PERIOD_COMMA_EXCLAMATION_SEMICOLON_TO_KAOMOJIS_SECOND,
                lambda: f" {FACES[random.randint(0, len(FACES) - 1)]}",
            )
        return input

    def map_that_to_dat(input: Word) -> Word:
        return input.replace(THAT_TO_DAT_LOWER, "dat").replace(THAT_TO_DAT_UPPER, "Dat")

    def map_th_to_f(input: Word) -> Word:
        return input.replace(TH_TO_F_LOWER, "f").replace(TH_TO_F_UPPER, "F")

    def map_le_to_wal(input: Word) -> Word:
        return input.replace(LE_TO_WAL, "wal")

    def map_ve_to_we(input: Word) -> Word:
        return input.replace(VE_TO_WE_LOWER, "we").replace(VE_TO_WE_UPPER, "We")

    def map_ry_to_wwy(input: Word) -> Word:
        return input.replace(RY_TO_WWY, "wwy")

    def map_r_or_l_to_w(input: Word) -> Word:
        return input.replace(RORL_TO_W_LOWER, "w").replace(RORL_TO_W_UPPER, "W")

    def map_ll_to_ww(input: Word) -> Word:
        return input.replace(LL_TO_WW, "ww")

    def map_vowel_or_r_except_o_l_to_wl(input: Word) -> Word:
        return input.replace(VOWEL_OR_R_EXCEPT_O_L_TO_WL_LOWER, "wl").replace(
            VOWEL_OR_R_EXCEPT_O_L_TO_WL_UPPER, "W\\1"
        )

    def map_old_to_owld(input: Word) -> Word:
        return input.replace(OLD_TO_OWLD_LOWER, "\\1wld").replace(
            OLD_TO_OWLD_UPPER, "OWLD"
        )

    def map_ol_to_owl(input: Word) -> Word:
        return input.replace(OL_TO_OWL_LOWER, "\\1wl").replace(OL_TO_OWL_UPPER, "OWL")

    def map_l_or_r_o_to_wo(input: Word) -> Word:
        return input.replace(LORR_O_TO_WO_LOWER, "wo").replace(
            LORR_O_TO_WO_UPPER, "W\\1"
        )

    def mapping_function_1(s1: str, s2: str) -> str:
        msg = s1
        if s2.upper() == s2:
            msg += "W"
        else:
            msg += "w"
        msg += s2
        return msg

    def map_specific_consonants_o_to_letter_and_wo(input: Word) -> Word:
        return input.replace(
            SPECIFIC_CONSONANTS_O_TO_LETTER_AND_WO_LOWER, "\\1wo"
        ).replace_with_func_multiple(
            SPECIFIC_CONSONANTS_O_TO_LETTER_AND_WO_UPPER, mapping_function_1
        )

    def map_v_or_w_le_to_wal(input: Word) -> Word:
        return input.replace(VORW_LE_TO_WAL, "wal")

    def map_fi_to_fwi(input: Word) -> Word:
        return input.replace(FI_TO_FWI_LOWER, "\\1wi").replace(FI_TO_FWI_UPPER, "FWI")

    def map_ver_to_wer(input: Word) -> Word:
        return input.replace(VER_TO_WER, "wer")

    def map_poi_to_pwoi(input: Word) -> Word:
        return input.replace(POI_TO_PWOI, "\\1woi")

    def map_specific_consonants_le_to_letter_and_wal(input: Word) -> Word:
        return input.replace(SPECIFIC_CONSONANTS_LE_TO_LETTER_AND_WAL, "\\1wal")

    def map_consonant_r_to_consonant_w(input: Word) -> Word:
        return input.replace(CONSONANT_R_TO_CONSONANT_W, "\\1w")

    def map_ly_to_wy(input: Word) -> Word:
        return input.replace(LY_TO_WY_LOWER, "wy").replace(LY_TO_WY_UPPER, "Wy")

    def map_ple_to_pwe(input: Word) -> Word:
        return input.replace(PLE_TO_PWE, "\\1we")

    def map_nr_to_nw(input: Word) -> Word:
        return input.replace(NR_TO_NW_LOWER, "\\1w").replace(NR_TO_NW_UPPER, "NW")

    def map_mem_to_mwem(input: Word) -> Word:
        return input.replace(MEM_TO_MWEM_UPPER, "mwem").replace(
            MEM_TO_MWEM_LOWER, "Mwem"
        )

    def unmap_nywo_to_nyo(input: Word) -> Word:
        return input.replace(NYWO_TO_NYO, "\\1yo")

    def map_fuc_to_fwuc(input: Word) -> Word:
        return input.replace(FUC_TO_FWUC, "\\1wuc")

    def map_mom_to_mwom(input: Word) -> Word:
        return input.replace(MOM_TO_MWOM, "\\1wom")

    def map_me_to_mwe(input: Word) -> Word:
        return input.replace(ME_TO_MWE_UPPER, "Mwe").replace(ME_TO_MWE_LOWER, "mwe")

    def map_n_vowel_to_ny(input: Word) -> Word:
        return (
            input.replace(N_VOWEL_TO_NY_FIRST, "ny\\1")
            .replace(N_VOWEL_TO_NY_SECOND, "Ny\\1")
            .replace(N_VOWEL_TO_NY_THIRD, "NY\\1")
        )

    def map_ove_to_uv(input: Word) -> Word:
        return input.replace(OVE_TO_UV_LOWER, "uv").replace(OVE_TO_UV_UPPER, "UV")

    def map_haha_to_hehe_xd(input: Word) -> Word:
        return input.replace(HAHA_TO_HEHE_XD, "hehe xD")

    def map_the_to_teh(input: Word) -> Word:
        return input.replace(THE_TO_TEH, "\\1eh")

    def map_you_to_u(input: Word) -> Word:
        return input.replace(YOU_TO_U_UPPER, "U").replace(YOU_TO_U_LOWER, "u")

    def map_time_to_tim(input: Word) -> Word:
        return input.replace(TIME_TO_TIM, "\\1im")

    def map_over_to_owor(input: Word) -> Word:
        return input.replace(OVER_TO_OWOR, "\\1wor")

    def map_worse_to_wose(input: Word) -> Word:
        return input.replace(WORSE_TO_WOSE, "\\1ose")

    def map_great_to_gwate(input: Word) -> Word:
        return input.replace(GREAT_TO_GWATE, "\\1wate")

    def map_aviat_to_awiat(input: Word) -> Word:
        return input.replace(AVIAT_TO_AWIAT, "\\1wiat")

    def map_dedicat_to_deditat(input: Word) -> Word:
        return input.replace(DEDICAT_TO_DEDITAT, "\\1editat")

    def map_remember_to_rember(input: Word) -> Word:
        return input.replace(REMEMBER_TO_REMBER, "\\1ember")

    def map_when_to_wen(input: Word) -> Word:
        return input.replace(WHEN_TO_WEN, "\\1en")

    def map_frightened_to_frigten(input: Word) -> Word:
        return input.replace(FRIGHTENED_TO_FRIGTEN, "\\1rigten")

    def map_meme_to_mem(input: Word) -> Word:
        return input.replace(MEME_TO_MEM_FIRST, "mem").replace(
            MEME_TO_MEM_SECOND, "Mem"
        )

    def map_feel_to_fell(input: Word) -> Word:
        return input.replace(FEEL_TO_FELL, "\\1ell")

    SPECIFIC_WORD_MAPPING_LIST = [
        map_fuc_to_fwuc,
        map_mom_to_mwom,
        map_time_to_tim,
        map_me_to_mwe,
        map_over_to_owor,
        map_ove_to_uv,
        map_haha_to_hehe_xd,
        map_the_to_teh,
        map_you_to_u,
        map_read_to_wead,
        map_worse_to_wose,
        map_great_to_gwate,
        map_aviat_to_awiat,
        map_dedicat_to_deditat,
        map_remember_to_rember,
        map_when_to_wen,
        map_frightened_to_frigten,
        map_meme_to_mem,
        map_feel_to_fell,
    ]
    UVU_MAPPING_LIST = [
        map_o_to_owo,
        map_ew_to_uwu,
        map_hey_to_hay,
        map_dead_to_ded,
        map_n_vowel_t_to_nd,
    ]
    UWU_MAPPING_LIST = [
        map_brackets_to_star_trails,
        map_period_comma_exclamation_semicolon_to_kaomojis,
        map_that_to_dat,
        map_th_to_f,
        map_le_to_wal,
        map_ve_to_we,
        map_ry_to_wwy,
        map_r_or_l_to_w,
    ]
    OWO_MAPPING_LIST = [
        map_n_vowel_to_ny,
        map_ll_to_ww,
        map_vowel_or_r_except_o_l_to_wl,
        map_old_to_owld,
        map_ol_to_owl,
        map_l_or_r_o_to_wo,
        map_specific_consonants_o_to_letter_and_wo,
        map_v_or_w_le_to_wal,
        map_fi_to_fwi,
        map_ver_to_wer,
        map_poi_to_pwoi,
        map_specific_consonants_le_to_letter_and_wal,
        map_consonant_r_to_consonant_w,
        map_ly_to_wy,
        map_ple_to_pwe,
        map_nr_to_nw,
        map_mem_to_mwem,
        unmap_nywo_to_nyo,
    ]
    words = [Word(s) for s in word_matches]
    spaces = [Word(s) for s in space_matches]

    def interleave_arrays(a: list, b: list) -> list:
        arr = []
        observed = a
        other = b
        temp = []
        while len(observed) > 0:
            arr.append(observed.pop(0))
            temp = observed
            observed = other
            other = temp
        if len(other) > 0:
            arr += other
        return arr

    def map_owoify_levels(word: Word, level: int) -> Word:
        for func in SPECIFIC_WORD_MAPPING_LIST:
            word = func(word)
        match level:
            case 0:
                for func in OWO_MAPPING_LIST:
                    word = func(word)
            case 1:
                for func in UWU_MAPPING_LIST:
                    word = func(word)
                for func in OWO_MAPPING_LIST:
                    word = func(word)
            case 2:
                for func in UVU_MAPPING_LIST:
                    word = func(word)
                for func in UWU_MAPPING_LIST:
                    word = func(word)
                for func in OWO_MAPPING_LIST:
                    word = func(word)
            case _:
                raise RuntimeError("The specified owoify level is not supported.")
        return word

    words = list(map(lambda w: map_owoify_levels(w, level), words))
    result = interleave_arrays(words, spaces)
    result_strings = list(map(lambda w: str(w), result))
    return "".join(result_strings)


def uwuify(source: str) -> str:
    """
    Equivalent to owoify at level 1
    """
    return owoify(source=source, level=1)


def uvuify(source: str) -> str:
    """
    Equivalent to owoify at level 2
    """
    return owoify(source=source, level=2)
