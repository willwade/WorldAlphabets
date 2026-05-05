#!/usr/bin/env python3
"""Generate data/tag_map.json: map all inflection tags to structured features.

Strategy:
1. Build a comprehensive part-to-feature dictionary (279 unique parts)
2. Parse each tag by splitting on '_' and classifying each part
3. Handle special patterns (Basque args, Bantu classes, possessor markers)
4. LLM fallback for genuinely ambiguous tags
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "inflections"
SCHEMA_PATH = REPO_ROOT / "data" / "feature_schema.json"
OUTPUT_PATH = REPO_ROOT / "data" / "tag_map.json"

# Each part maps to a list of (dimension, value) pairs.
# Some parts are context-dependent and handled in the parser.
PART_MAP: dict[str, list[tuple[str, str]]] = {
    # === POS ===
    "v": [("pos", "verb")],
    "n": [("pos", "noun")],
    "adj": [("pos", "adjective")],
    "adv": [("pos", "adverb")],
    "pron": [("pos", "pronoun")],
    "prep": [("pos", "preposition")],
    "det": [("pos", "determiner")],
    "conj": [("pos", "conjunction")],
    "num": [("pos", "numeral")],
    "intj": [("pos", "interjection")],
    "adp": [("pos", "adposition")],
    "part": [("pos", "particle")],
    "art": [("pos", "determiner")],
    # === Person ===
    "1": [("person", "1")],
    "2": [("person", "2")],
    "3": [("person", "3")],
    "4": [("person", "4")],
    "0": [("person", "0")],
    "1s": [("person", "1"), ("number", "singular")],
    "2s": [("person", "2"), ("number", "singular")],
    "3s": [("person", "3"), ("number", "singular")],
    "1p": [("person", "1"), ("number", "plural")],
    "2p": [("person", "2"), ("number", "plural")],
    "3p": [("person", "3"), ("number", "plural")],
    # === Number ===
    "sg": [("number", "singular")],
    "pl": [("number", "plural")],
    "du": [("number", "dual")],
    # === Gender ===
    "masc": [("gender", "masculine")],
    "fem": [("gender", "feminine")],
    "neut": [("gender", "neuter")],
    # === Case ===
    "nom": [("case", "nominative")],
    "acc": [("case", "accusative")],
    "dat": [("case", "dative")],
    "gen": [("case", "genitive")],
    "abl": [("case", "ablative")],
    "loc": [("case", "locative")],
    "ins": [("case", "instrumental")],
    "voc": [("case", "vocative")],
    "ess": [("case", "essive")],
    "all": [("case", "allative")],
    "com": [("case", "comitative")],
    "trans": [("case", "translative")],
    "ben": [("case", "benefactive")],
    "perl": [("case", "perlative")],
    "erg": [("case", "ergative")],
    "abs": [("case", "absolutive")],
    "inst": [("case", "instrumental")],
    "term": [("case", "terminative")],
    "frml": [("case", "formal")],
    "sociative": [("case", "sociative")],
    "distr": [("case", "distributive")],
    "immed": [("case", "immediate")],
    "prox": [("case", "proximal")],
    "rmt": [("case", "remotive")],
    "remt": [("case", "remotive")],
    "rct": [("case", "remotive")],
    "foc": [("focus", "yes")],
    "foreg": [("case", "proximal")],
    "sim": [("case", "imitative")],
    "prp": [("case", "proximal")],
    "byway": [("case", "perlative")],
    "incl": [("case", "inclusive")],
    "excl": [("case", "exclusive")],
    # === Tense ===
    "prs": [("tense", "present")],
    "pst": [("tense", "past")],
    "fut": [("tense", "future")],
    "pret": [("tense", "preterite")],
    "aor": [("tense", "aorist")],
    "npst": [("tense", "nonpast")],
    # === Mood ===
    "ind": [("mood", "indicative")],
    "sbjv": [("mood", "subjunctive")],
    "imp": [("mood", "imperative")],
    "cond": [("mood", "conditional")],
    "pot": [("mood", "potential")],
    "opt": [("mood", "optative")],
    "sub": [("mood", "subjunctive")],
    "hyp": [("mood", "hypothetical")],
    "adm": [("mood", "admirative")],
    # === Aspect ===
    "ipfv": [("aspect", "imperfective")],
    "pfv": [("aspect", "perfective")],
    "prog": [("aspect", "progressive")],
    "hab": [("aspect", "habitual")],
    "prf": [("aspect", "perfect")],
    "prosp": [("aspect", "prospective")],
    "iter": [("aspect", "iterative")],
    "freq": [("aspect", "frequentive")],
    "dur": [("aspect", "durative")],
    # === Voice ===
    "act": [("voice", "active")],
    "pass": [("voice", "passive")],
    "mid": [("voice", "middle")],
    # === Definiteness ===
    "def": [("definiteness", "definite")],
    "ndef": [("definiteness", "indefinite")],
    "indef": [("definiteness", "indefinite")],
    "indf": [("definiteness", "indefinite")],
    "infm": [("definiteness", "indefinite")],
    # === Degree ===
    "cmpr": [("degree", "comparative")],
    "sprl": [("degree", "superlative")],
    # === Polarity ===
    "neg": [("polarity", "negative")],
    "pos": [("polarity", "positive")],
    # === Verb form ===
    "ptcp": [("verbform", "participle")],
    "cvb": [("verbform", "converb")],
    "ger": [("verbform", "gerund")],
    "inf": [("verbform", "infinitive")],
    "sup": [("verbform", "supine")],
    "pctp": [("verbform", "participle")],
    "msdr": [("verbform", "masdar")],
    "masv": [("verbform", "masdar")],
    # === Finiteness ===
    "fin": [("finiteness", "finite")],
    "nfin": [("finiteness", "nonfinite")],
    # === Formality ===
    "form": [("formality", "formal")],
    "form2": [("formality", "formal")],
    "pol": [("formality", "polite")],
    "elev": [("formality", "elevated")],
    "humb": [("formality", "humble")],
    "col": [("formality", "colloquial")],
    # === Evidentiality ===
    "decl": [("evidentiality", "declarative")],
    "infr": [("evidentiality", "inferential")],
    "nfh": [("evidentiality", "nonfirsthand")],
    "quot": [("evidentiality", "quotative")],
    # === English flat tags ===
    "base": [],
    "plural": [("number", "plural")],
    "singular": [("number", "singular")],
    "possessive": [("case", "genitive")],
    "negative": [("polarity", "negative")],
    "negation": [("polarity", "negative")],
    "objective": [("case", "accusative")],
    "reflexive": [("voice", "middle")],
    "adjective": [("pos", "adjective")],
    "infinitive": [("verbform", "infinitive")],
    "participle": [("verbform", "participle")],
    "present": [("tense", "present")],
    "comparative": [("degree", "comparative")],
    "superlative": [("degree", "superlative")],
    "simple": [],
    "past": [("tense", "past")],
    "gerund": [("verbform", "gerund")],
    "accusative": [("case", "accusative")],
    "dative": [("case", "dative")],
    "feminine": [("gender", "feminine")],
    "masculine": [("gender", "masculine")],
    "neuter": [("gender", "neuter")],
    "genitive": [("case", "genitive")],
    "comitative": [("case", "comitative")],
    "prepositional": [("case", "prepositional")],
    "feminine_singular": [("gender", "feminine"), ("number", "singular")],
    "feminine_plural": [("gender", "feminine"), ("number", "plural")],
    "masculine_singular": [("gender", "masculine"), ("number", "singular")],
    "masculine_plural": [("gender", "masculine"), ("number", "plural")],
    # === Misc known parts ===
    "oblig": [("obligation", "obligative")],
    "pro": [("verbform", "participle")],
    "intr": [("voice", "active")],
    "inter": [("degree", "comparative")],
    "on": [],
    "at": [],
    "in": [],
    "lit": [],
    "non": [],
    "prt": [("pos", "particle")],
    "int": [("pos", "interjection")],
    "cf": [("comparison_form", "cf")],
    "fh": [("evidentiality", "nonfirsthand")],
    "extra": [],
    "strong": [],
    "weak": [],
    "hod": [],
    "perm": [("derivational", "permissive")],
    "inten": [("derivational", "intensive")],
    "purp": [],
    "ded": [("evidentiality", "inferential")],
    "anim": [("animacy", "animate")],
    "inan": [("animacy", "inanimate")],
    "refl": [("derivational", "reflexive")],
    "appl": [("derivational", "applicative")],
    "caus": [("derivational", "causative")],
    "recp": [("derivational", "reciprocal")],
    "agt": [("case", "agentive")],
    "tr": [("clitic_type", "transitive")],
    "vers": [("derivational", "versive")],
    "ab": [],
    "ac1": [("action_class", "1")],
    "ac2": [("action_class", "2")],
    "ac3": [("action_class", "3")],
}

# Basque argument markers: argabs, argerg, argio, argno
BASQUE_ARG_MAP = {
    "argabs1": [("arg_abs", "1")],
    "argabs2": [("arg_abs", "2")],
    "argabs3": [("arg_abs", "3")],
    "argabssg": [("arg_abs", "sg")],
    "argabspl": [("arg_abs", "pl")],
    "argabsinfm": [("arg_abs", "indef")],
    "argerg1": [("arg_erg", "1")],
    "argerg2": [("arg_erg", "2")],
    "argerg3": [("arg_erg", "3")],
    "argergsg": [("arg_erg", "sg")],
    "argergpl": [("arg_erg", "pl")],
    "argerginfm": [("arg_erg", "indef")],
    "argergmasc": [("arg_erg", "masc")],
    "argergfem": [("arg_erg", "fem")],
    "argio1": [("arg_dat", "1")],
    "argio2": [("arg_dat", "2")],
    "argio3": [("arg_dat", "3")],
    "argiosg": [("arg_dat", "sg")],
    "argiopl": [("arg_dat", "pl")],
    "argioinfm": [("arg_dat", "indef")],
    "argiomasc": [("arg_dat", "masc")],
    "argiofem": [("arg_dat", "fem")],
    "argno1s": [("arg_other", "1sg")],
    "argno2s": [("arg_other", "2sg")],
    "argno3s": [("arg_other", "3sg")],
    "argno1p": [("arg_other", "1pl")],
    "argno2p": [("arg_other", "2pl")],
    "argno3p": [("arg_other", "3pl")],
}

# Bantu noun classes
BANTU_MAP = {}
for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 17]:
    BANTU_MAP[f"bantu{i}"] = [("noun_class", str(i))]

# Possessor markers (Swahili/Zulu): pss1s, pss3sm, pssb6, etc.
POSSESSOR_RE = re.compile(
    r"^pss(\d)([sp])([mf]?)$"
)
POSSESSOR_B_RE = re.compile(r"^pssb(\d+)$")


def parse_possessor(part: str) -> list[tuple[str, str]] | None:
    m = POSSESSOR_RE.match(part)
    if m:
        person = m.group(1)
        num = "sg" if m.group(2) == "s" else "pl"
        result = [
            ("possessor_person", person),
            ("possessor_number", num),
        ]
        if m.group(3):
            result.append(("possessor_gender", m.group(3)))
        return result
    m = POSSESSOR_B_RE.match(part)
    if m:
        return [("noun_class", m.group(1))]
    return None


# Quechua derivational markers
QUECHUA_MAP = {
    "causv": [("derivational", "causative")],
    "compv": [("derivational", "competitive")],
    "exclv": [("derivational", "excessive")],
    "beadj": [("derivational", "be_adjective")],
    "geadj": [("derivational", "ge_adjective")],
    "priv": [("derivational", "privative")],
    "propr": [("derivational", "proprietive")],
    "eqtv": [("derivational", "equative")],
    "vers": [("derivational", "versive")],
    "distr": [("derivational", "distributive")],
    "trans": [("derivational", "translocative")],
    "immed": [("derivational", "immediate")],
    "appl": [("derivational", "applicative")],
    "caus": [("derivational", "causative")],
    "iter": [("derivational", "iterative")],
    "freq": [("derivational", "frequentive")],
    "refl": [("derivational", "reflexive")],
    "recp": [("derivational", "reciprocal")],
    "excl": [("clusivity", "exclusive")],
    "incl": [("clusivity", "inclusive")],
}

# Turkish lgspec markers
LGSPEC_RE = re.compile(r"^lgspec(\d+)$")


def parse_lgspec(part: str) -> list[tuple[str, str]] | None:
    m = LGSPEC_RE.match(part)
    if m:
        return [("lgspec", m.group(1))]
    return None


# Spatial directions (English)
SPATIAL_MAP = {
    "N": [("spatial", "north")],
    "S": [("spatial", "south")],
    "E": [("spatial", "east")],
    "W": [("spatial", "west")],
    "NE": [("spatial", "northeast")],
    "NW": [("spatial", "northwest")],
    "SE": [("spatial", "southeast")],
    "SW": [("spatial", "southwest")],
}

# Merge all maps
ALL_PART_MAP: dict[str, list[tuple[str, str]]] = {}
ALL_PART_MAP.update(PART_MAP)
ALL_PART_MAP.update(BASQUE_ARG_MAP)
ALL_PART_MAP.update(BANTU_MAP)
ALL_PART_MAP.update(QUECHUA_MAP)
ALL_PART_MAP.update(SPATIAL_MAP)

# Multi-part English tags (tags that are a single string, no underscores)
FLAT_TAG_MAP: dict[str, list[tuple[str, str]]] = {
    "past_participle": [
        ("verbform", "participle"),
        ("tense", "past"),
    ],
    "present_participle": [
        ("verbform", "participle"),
        ("tense", "present"),
    ],
    "past": [("tense", "past")],
    "present": [("tense", "present")],
    "simple_past": [("tense", "past")],
    "simple_present": [("tense", "present")],
    "plural_present": [
        ("number", "plural"),
        ("tense", "present"),
    ],
    "feminine_singular": [
        ("gender", "feminine"),
        ("number", "singular"),
    ],
    "feminine_plural": [
        ("gender", "feminine"),
        ("number", "plural"),
    ],
    "masculine_singular": [
        ("gender", "masculine"),
        ("number", "singular"),
    ],
    "masculine_plural": [
        ("gender", "masculine"),
        ("number", "plural"),
    ],
    "negative_comparative": [
        ("polarity", "negative"),
        ("degree", "comparative"),
    ],
    "negative_superlative": [
        ("polarity", "negative"),
        ("degree", "superlative"),
    ],
    "3rd_person_singular": [
        ("person", "3"),
        ("number", "singular"),
    ],
    "possessive": [("case", "genitive")],
    "plural": [("number", "plural")],
    "singular": [("number", "singular")],
    "infinitive": [("verbform", "infinitive")],
    "comparative": [("degree", "comparative")],
    "superlative": [("degree", "superlative")],
    "base": [],
    "negation": [("polarity", "negative")],
    "negative": [("polarity", "negative")],
    "objective": [("case", "accusative")],
    "reflexive": [("voice", "middle")],
    "gerund": [("verbform", "gerund")],
    "participle": [("verbform", "participle")],
    "neuter": [("gender", "neuter")],
    "adjective": [("pos", "adjective")],
}

# Ambiguous parts that depend on context
AMBIGUOUS_PARTS = {
    "comp": [("degree", "comparative")],  # could be comparative or competitive
    "sup": [("verbform", "supine")],  # could be superlative or supine
}


def _resolve_part(
    part: str,
    features: dict[str, str],
    is_last: bool,
    pos_known: bool,
) -> bool:
    """Try to resolve a single part. Returns True if resolved."""
    # Check all maps
    if part in ALL_PART_MAP:
        for dim, val in ALL_PART_MAP[part]:
            features[dim] = val
        return True

    # Check possessor markers
    poss = parse_possessor(part)
    if poss:
        for dim, val in poss:
            features[dim] = val
        return True

    # Check lgspec markers
    lg = parse_lgspec(part)
    if lg:
        for dim, val in lg:
            features[dim] = val
        return True

    # Check ambiguous parts
    if part in AMBIGUOUS_PARTS:
        for dim, val in AMBIGUOUS_PARTS[part]:
            if dim not in features:
                features[dim] = val
        return True

    return False


def parse_tag(tag: str) -> dict[str, str]:
    """Parse a single tag into structured features."""
    if tag in FLAT_TAG_MAP:
        pairs = FLAT_TAG_MAP[tag]
        return {dim: val for dim, val in pairs}

    parts = tag.split("_")
    features: dict[str, str] = {}
    pending_digits: list[tuple[int, str]] = []

    # First pass: resolve all non-digit parts, collect digits
    for i, part in enumerate(parts):
        if part.isdigit() or (len(part) == 1 and part in "01234"):
            pending_digits.append((i, part))
            continue
        _resolve_part(part, features, False, False)

    # Second pass: resolve digits based on context
    pos_val = features.get("pos", "")
    for idx, digit in pending_digits:
        is_last = idx == len(parts) - 1
        if digit in ("1", "2", "3", "0", "4"):
            if not is_last:
                # Digit followed by more parts → person
                features["person"] = digit
            elif pos_val == "verb" and digit in ("1", "2", "3", "0"):
                # Verb tag ending with person digit → person
                features["person"] = digit
            elif digit == "1" and not pos_val:
                # No POS detected (e.g. extra_1) → variant
                features["variant"] = digit
            else:
                # Non-verb ending with digit → variant
                features["variant"] = digit
        else:
            features["variant"] = digit

    return features


def collect_all_tags() -> tuple[set[str], dict[str, set[str]]]:
    """Collect all unique tags across all locales."""
    all_tags: set[str] = set()
    tag_locales: dict[str, set[str]] = {}

    for d in sorted(DATA_DIR.iterdir()):
        words_f = d / "words.json"
        if not words_f.exists():
            continue
        data = json.loads(words_f.read_text())
        for word, info in data.items():
            if not isinstance(info, dict):
                continue
            for k in info.get("inflections", {}):
                if k != "regulars":
                    all_tags.add(k)
                    tag_locales.setdefault(k, set()).add(d.name)

    return all_tags, tag_locales


def validate_features(
    features: dict[str, str],
    schema: dict,
) -> list[str]:
    """Validate features against schema. Returns list of warnings."""
    warnings = []
    dims = schema.get("dimensions", {})
    for dim, val in features.items():
        if dim not in dims:
            warnings.append(f"Unknown dimension: {dim}")
            continue
        valid_vals = dims[dim].get("values", [])
        if valid_vals and val not in valid_vals:
            warnings.append(f"Invalid value '{val}' for dimension '{dim}'")
    return warnings


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    all_tags, tag_locales = collect_all_tags()

    print(f"Found {len(all_tags)} unique tags across {len(set().union(*tag_locales.values()))} locales")

    tag_map: dict[str, dict] = {}
    unresolved: list[str] = []
    stats: Counter[str] = Counter()

    for tag in sorted(all_tags):
        features = parse_tag(tag)
        warnings = validate_features(features, schema)

        if warnings:
            stats["has_warnings"] += 1
            if "extra" in features:
                stats["has_extra"] += 1
                unresolved.append(tag)

        tag_map[tag] = {
            "features": features,
            "locales": sorted(tag_locales.get(tag, [])),
        }

        if not warnings:
            stats["clean"] += 1

    # Print stats
    print("\nResults:")
    print(f"  Clean mappings: {stats['clean']}")
    print(f"  With warnings: {stats['has_warnings']}")
    print(f"  With unresolved parts (extra): {stats['has_extra']}")

    if unresolved:
        print(f"\n{len(unresolved)} tags with unresolved parts:")
        for tag in unresolved[:30]:
            info = tag_map[tag]
            print(f"  {tag} → {info['features']}")

    # Write output
    OUTPUT_PATH.write_text(
        json.dumps(tag_map, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"\nWrote {OUTPUT_PATH} ({len(tag_map)} tags)")

    # Report unresolved tags for LLM pass
    if unresolved:
        unresolved_path = REPO_ROOT / "data" / "tag_map_unresolved.json"
        unresolved_data = {tag: tag_map[tag] for tag in unresolved}
        unresolved_path.write_text(
            json.dumps(unresolved_data, indent=2, ensure_ascii=False)
            + "\n"
        )
        print(f"Wrote {len(unresolved)} unresolved tags to {unresolved_path}")

    return 0 if not unresolved else 1


if __name__ == "__main__":
    sys.exit(main())
