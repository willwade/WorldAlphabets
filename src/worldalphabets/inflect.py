"""Inflection rule engine and data-loading helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any, Dict, List, Optional

_INFLECTION_DIR = files("worldalphabets") / "data" / "inflections"
_TAG_MAP_PATH = files("worldalphabets") / "data" / "tag_map.json"

_cache: Dict[str, Any] = {}


def _inflection_dir() -> Path:
    return Path(str(_INFLECTION_DIR))


def clear_cache() -> None:
    _cache.clear()


def _load_json(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _resolve_locale(locale: str, filename: str) -> Path:
    path = _inflection_dir() / locale / filename
    if path.is_file():
        return path
    if "-" in locale:
        base = locale.split("-", 1)[0]
        base_path = _inflection_dir() / base / filename
        if base_path.is_file():
            return base_path
    raise FileNotFoundError(
        f"Inflection data for locale '{locale}' not found"
    )


def load_index() -> Dict[str, Any]:
    key = "__inflection_index__"
    if key not in _cache:
        path = _inflection_dir() / "index.json"
        if path.is_file():
            _cache[key] = _load_json(path)
        else:
            _cache[key] = {
                "_type": "inflection_index",
                "_version": "0.1",
                "locales": {},
            }
    return _cache[key]


def get_available_locales() -> List[str]:
    index = load_index()
    locales = index.get("locales", {})
    if not isinstance(locales, dict):
        return []
    return sorted(str(loc) for loc in locales)


def load_words(locale: str) -> Dict[str, Any]:
    cache_key = f"words:{locale}"
    if cache_key not in _cache:
        path = _resolve_locale(locale, "words.json")
        _cache[cache_key] = _load_json(path)
    return _cache[cache_key]


def load_rules(locale: str) -> Dict[str, Any]:
    cache_key = f"rules:{locale}"
    if cache_key not in _cache:
        path = _resolve_locale(locale, "rules.json")
        _cache[cache_key] = _load_json(path)
    return _cache[cache_key]


def load_data(locale: str) -> Dict[str, Dict[str, Any]]:
    return {"words": load_words(locale), "rules": load_rules(locale)}


def load_tag_map() -> Dict[str, Any]:
    key = "__tag_map__"
    if key not in _cache:
        path = Path(str(_TAG_MAP_PATH))
        if path.is_file():
            _cache[key] = _load_json(path)
        else:
            _cache[key] = {}
    return _cache[key]


def get_features(tag: str) -> Optional[Dict[str, str]]:
    tag_map = load_tag_map()
    entry = tag_map.get(tag)
    if not isinstance(entry, dict):
        return None
    return entry.get("features")


@dataclass
class LocaleSummary:
    locale: str
    word_count: int
    rule_count: int
    test_count: int
    pos_types: List[str] = field(default_factory=list)
    inflection_keys: List[str] = field(default_factory=list)


def get_summary(locale: str) -> LocaleSummary:
    words_data = load_words(locale)
    rules_data = load_rules(locale)

    pos_types: set[str] = set()
    inflection_keys: set[str] = set()
    word_count = 0
    for key, entry in words_data.items():
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        word_count += 1
        types = entry.get("types", [])
        if isinstance(types, list):
            pos_types.update(types)
        forms = entry.get("inflections", {})
        if isinstance(forms, dict):
            inflection_keys.update(k for k in forms if k != "regulars")

    rules = rules_data.get("rules", [])
    tests = rules_data.get("tests", [])

    return LocaleSummary(
        locale=locale,
        word_count=word_count,
        rule_count=len(rules) if isinstance(rules, list) else 0,
        test_count=len(tests) if isinstance(tests, list) else 0,
        pos_types=sorted(pos_types),
        inflection_keys=sorted(inflection_keys),
    )


def get_word_forms(locale: str, word: str) -> Optional[Dict[str, Any]]:
    words = load_words(locale)
    entry = words.get(word)
    return entry if isinstance(entry, dict) else None


def inflect_word(
    locale: str, word: str, inflection: str
) -> Optional[str]:
    entry = get_word_forms(locale, word)
    if entry is None:
        return None
    if inflection == "base":
        base = entry.get("base")
        return base if isinstance(base, str) else word
    forms = entry.get("inflections")
    if not isinstance(forms, dict):
        return None
    value = forms.get(inflection)
    return value if isinstance(value, str) else None


def _item_matches(check: Dict[str, Any], item: Dict[str, Any]) -> bool:
    label = str(item.get("word", "")).lower()
    if isinstance(check.get("words"), list):
        matching = label in check["words"]
    elif isinstance(check.get("type"), str):
        types = item.get("types", [])
        matching = isinstance(types, list) and check["type"] in types
    else:
        matching = True
    if matching and isinstance(check.get("match"), str):
        matching = re.search(check["match"], label) is not None
    if matching and isinstance(check.get("non_match"), str):
        matching = re.search(check["non_match"], label) is None
    return matching


def _matches_rule(
    rule: Dict[str, Any], buttons: List[Dict[str, Any]]
) -> bool | Dict[str, Any]:
    lookback = rule.get("lookback", [])
    if not isinstance(lookback, list):
        return False
    history_idx = len(buttons) - 1
    valid = True
    condenses: List[int] = []
    for idx in range(len(lookback) - 1, -1, -1):
        check = lookback[idx]
        pre_check = lookback[idx - 1] if idx > 0 else None
        if not isinstance(check, dict):
            return False
        item = buttons[history_idx] if history_idx >= 0 else None
        if item is None:
            if not check.get("optional"):
                valid = False
        else:
            matching = _item_matches(check, item)
            pre_matching = (
                isinstance(pre_check, dict)
                and _item_matches(pre_check, item)
            )
            pre_optional = (
                pre_check.get("optional")
                if isinstance(pre_check, dict)
                else None
            )
            if (
                matching
                and check.get("optional")
                and pre_matching
                and not pre_optional
            ):
                matching = False
            if matching:
                if check.get("condense"):
                    condenses.append(history_idx)
                history_idx -= 1
            elif not check.get("optional"):
                valid = False
        if not valid:
            break
    if valid and condenses:
        return {"condense_items": condenses}
    return bool(valid)


@dataclass
class JoinResult:
    result: str
    rule_id: Optional[str] = None
    reason: Optional[str] = None
    replaces_pair: bool = False


def join_words(
    locale_or_rules: str | Dict[str, Any],
    prev: str,
    next_word: str,
) -> Optional[JoinResult]:
    if isinstance(locale_or_rules, str):
        rules_data = load_rules(locale_or_rules)
    else:
        rules_data = locale_or_rules

    join_rules = rules_data.get("join", [])
    if not isinstance(join_rules, list):
        return None

    prev_lower = prev.lower()
    next_lower = next_word.lower()

    for rule in join_rules:
        if not isinstance(rule, dict):
            continue

        prev_list = rule.get("prev", [])
        if isinstance(prev_list, str):
            prev_list = [prev_list]
        if not isinstance(prev_list, list) or prev_lower not in [
            p.lower() if isinstance(p, str) else "" for p in prev_list
        ]:
            continue

        next_exact = rule.get("next")
        next_match = rule.get("next_match")

        matched = False
        if isinstance(next_exact, list):
            matched = next_lower in [
                n.lower() if isinstance(n, str) else "" for n in next_exact
            ]
        elif isinstance(next_exact, str):
            matched = next_lower == next_exact.lower()

        if not matched and isinstance(next_match, str):
            try:
                matched = bool(re.search(next_match, next_lower))
            except re.error:
                continue

        if not matched:
            continue

        result_template = rule.get("result", "{prev} {next}")
        result_str = (
            result_template.replace("{prev}", prev)
            .replace("{next}", next_word)
        )

        return JoinResult(
            result=result_str,
            rule_id=rule.get("id"),
            reason=rule.get("reason"),
            replaces_pair=result_template != "{prev} {next}",
        )

    return None


@dataclass
class LookupResult:
    word: str
    replacement: Optional[str] = None
    rule_id: Optional[str] = None
    rule_type: Optional[str] = None
    inflection: Optional[str] = None
    condense_items: Optional[List[int]] = None


def _build_word_list(
    words_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    words: List[Dict[str, Any]] = []
    for word, entry in words_data.items():
        if word.startswith("_") or not isinstance(entry, dict):
            continue
        item = dict(entry)
        item["word"] = word
        words.append(item)
    return words


def lookup_word(
    locale_or_words: str | Dict[str, Any],
    word: str,
    prior_words: str = "",
    rules_data: Optional[Dict[str, Any]] = None,
) -> LookupResult:
    if isinstance(locale_or_words, str):
        words_data = load_words(locale_or_words)
        if rules_data is None:
            rules_data = load_rules(locale_or_words)
    else:
        words_data = locale_or_words
        if rules_data is None:
            rules_data = {"rules": [], "tests": []}

    words = _build_word_list(words_data)
    rules = rules_data.get("rules", [])
    if not isinstance(rules, list):
        rules = []

    prior_buttons: List[Dict[str, Any]] = []
    for part in prior_words.split():
        found = next(
            (w for w in words if w.get("word") == part), None
        )
        prior_buttons.append(found or {"word": part})

    found_words = [w for w in words if w.get("word") == word]
    if not found_words:
        return LookupResult(word=word)

    found_types: Dict[str, bool] = {}
    matching_rules: List[Dict[str, Any]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rule_type = rule.get("type")
        if not isinstance(rule_type, str):
            continue
        if found_types.get(rule_type) and rule_type != "override":
            continue
        matches = _matches_rule(rule, prior_buttons)
        if matches:
            matched_rule = dict(rule)
            if isinstance(matches, dict):
                matched_rule.update(matches)
            matching_rules.append(matched_rule)
            found_types[rule_type] = True

    first = dict(found_words[0])
    inflections: Dict[str, Any] = {}
    for rule in matching_rules:
        if (
            rule.get("type") == "override"
            and isinstance(rule.get("overrides"), dict)
        ):
            for key, value in rule["overrides"].items():
                inflections.setdefault(
                    key,
                    {
                        "type": "override",
                        "word": value,
                        "id": rule.get("id"),
                        "condense_items": rule.get("condense_items"),
                    },
                )
        else:
            rule_type = rule.get("type")
            if isinstance(rule_type, str):
                inflections[rule_type] = rule

    replacement = None
    rule_id = None
    rule_type_out = None
    inflection_out = None
    condense_items = None

    found_word_value = first.get("word")
    direct = (
        inflections.get(found_word_value)
        if isinstance(found_word_value, str)
        else None
    )
    if isinstance(direct, dict) and direct.get("word"):
        replacement = direct["word"]
        rule_id = direct.get("id")
        condense_items = direct.get("condense_items")
    else:
        replacement_rule = None
        types = first.get("types", [])
        if isinstance(types, list):
            for part in types:
                if part in inflections:
                    replacement_rule = replacement_rule or inflections[part]
        if isinstance(replacement_rule, dict):
            forms = first.get("inflections", {})
            inflection = replacement_rule.get("inflection")
            if isinstance(forms, dict) and isinstance(inflection, str):
                replacement = forms.get(inflection) or first.get("word")
                inflection_out = inflection
            else:
                replacement = first.get("word")
            rule_id = replacement_rule.get("id")
            rule_type_out = inflection
            condense_items = replacement_rule.get("condense_items")

    return LookupResult(
        word=word,
        replacement=replacement,
        rule_id=rule_id,
        rule_type=rule_type_out,
        inflection=inflection_out,
        condense_items=condense_items,
    )


def apply_rules(
    locale: str, text: str, rules_data: Optional[Dict[str, Any]] = None
) -> str:
    tokens = text.split()
    if not tokens:
        return text

    words_data = load_words(locale)
    if rules_data is None:
        rules_data = load_rules(locale)

    results: List[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]

        if results:
            prev_token = tokens[i - 1] if i > 0 else ""
            jr = join_words(rules_data, prev_token, token)
            if jr and jr.replaces_pair:
                results.pop()
                results.append(jr.result)
                i += 1
                continue

        prior = " ".join(tokens[:i])
        result = lookup_word(words_data, token, prior, rules_data)
        if result.replacement:
            if result.condense_items is not None:
                prior_tokens = results[:]
                kept = [
                    w
                    for idx, w in enumerate(prior_tokens)
                    if idx not in result.condense_items
                ]
                results.clear()
                results.extend(kept)
                results.append(result.replacement)
            else:
                results.append(result.replacement)
        else:
            results.append(token)
        i += 1

    return " ".join(results)


@dataclass
class RenderedToken:
    index: int
    base: str
    surface: str
    rule_id: Optional[str] = None
    rule_type: Optional[str] = None
    inflection: Optional[str] = None
    join_applied: Optional[str] = None


@dataclass
class RenderDiff:
    index: int
    old_surface: Optional[str]
    new_surface: str
    kind: str = "change"


@dataclass
class RenderSnapshot:
    text: str
    tokens: List[RenderedToken] = field(default_factory=list)
    diffs: List[RenderDiff] = field(default_factory=list)


class SentenceBuffer:
    def __init__(
        self,
        locale: str,
        words_data: Optional[Dict[str, Any]] = None,
        rules_data: Optional[Dict[str, Any]] = None,
    ):
        self.locale = locale
        if words_data is None:
            words_data = load_words(locale)
        if rules_data is None:
            rules_data = load_rules(locale)
        self._words_data = words_data
        self._rules_data = rules_data
        self._words_list = _build_word_list(words_data)
        self._tokens: List[str] = []
        self._last_surfaces: List[str] = []

    def push(self, word: str) -> RenderSnapshot:
        self._tokens.append(word)
        return self.render_snapshot()

    def insert(self, index: int, word: str) -> RenderSnapshot:
        index = max(0, min(index, len(self._tokens)))
        self._tokens.insert(index, word)
        return self.render_snapshot()

    def update(self, index: int, word: str) -> RenderSnapshot:
        if index < 0 or index >= len(self._tokens):
            raise IndexError(f"index {index} out of range")
        self._tokens[index] = word
        return self.render_snapshot()

    def remove(self, index: int) -> RenderSnapshot:
        if index < 0 or index >= len(self._tokens):
            raise IndexError(f"index {index} out of range")
        self._tokens.pop(index)
        return self.render_snapshot()

    def clear(self) -> None:
        self._tokens.clear()
        self._last_surfaces.clear()

    def render(self) -> str:
        return self.render_snapshot().text

    def render_tokens(self) -> List[RenderedToken]:
        return self.render_snapshot().tokens

    def render_snapshot(self) -> RenderSnapshot:
        rendered = self._render_all()
        diffs = self._compute_diffs(self._last_surfaces, rendered)
        surfaces = [t.surface for t in rendered]
        self._last_surfaces = surfaces
        text = " ".join(surfaces)
        return RenderSnapshot(text=text, tokens=rendered, diffs=diffs)

    def __len__(self) -> int:
        return len(self._tokens)

    def token_at(self, index: int) -> str:
        if index < 0 or index >= len(self._tokens):
            raise IndexError(f"index {index} out of range")
        return self._tokens[index]

    @property
    def tokens(self) -> List[str]:
        return list(self._tokens)

    def _render_all(self) -> List[RenderedToken]:
        if not self._tokens:
            return []

        rules = self._rules_data.get("rules", [])
        if not isinstance(rules, list):
            rules = []
        join_rules = self._rules_data.get("join", [])
        if not isinstance(join_rules, list):
            join_rules = []

        raw_tokens: List[RenderedToken] = []

        for i, token in enumerate(self._tokens):
            prior_parts = self._tokens[:i]
            prior_buttons = self._build_prior_buttons(prior_parts)

            found = [w for w in self._words_list if w.get("word") == token]
            if not found:
                raw_tokens.append(
                    RenderedToken(index=i, base=token, surface=token)
                )
                continue

            replacement, rule_id, rule_type, inflection = (
                self._apply_rules_for_token(
                    token, found, prior_buttons, rules
                )
            )

            surface = replacement if replacement else token
            raw_tokens.append(
                RenderedToken(
                    index=i,
                    base=token,
                    surface=surface,
                    rule_id=rule_id,
                    rule_type=rule_type,
                    inflection=inflection,
                )
            )

        if not join_rules:
            return raw_tokens

        return self._apply_joins(raw_tokens, join_rules)

    def _build_prior_buttons(
        self, prior_parts: List[str]
    ) -> List[Dict[str, Any]]:
        buttons: List[Dict[str, Any]] = []
        for part in prior_parts:
            found = next(
                (w for w in self._words_list if w.get("word") == part),
                None,
            )
            buttons.append(found or {"word": part})
        return buttons

    def _apply_rules_for_token(
        self,
        token: str,
        found_words: List[Dict[str, Any]],
        prior_buttons: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        found_types: Dict[str, bool] = {}
        matching_rules: List[Dict[str, Any]] = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            rule_type = rule.get("type")
            if not isinstance(rule_type, str):
                continue
            if found_types.get(rule_type) and rule_type != "override":
                continue
            matches = _matches_rule(rule, prior_buttons)
            if matches:
                matched_rule = dict(rule)
                if isinstance(matches, dict):
                    matched_rule.update(matches)
                matching_rules.append(matched_rule)
                found_types[rule_type] = True

        first = dict(found_words[0])
        infl: Dict[str, Any] = {}
        for rule in matching_rules:
            if (
                rule.get("type") == "override"
                and isinstance(rule.get("overrides"), dict)
            ):
                for key, value in rule["overrides"].items():
                    infl.setdefault(
                        key,
                        {
                            "type": "override",
                            "word": value,
                            "id": rule.get("id"),
                            "condense_items": rule.get("condense_items"),
                        },
                    )
            else:
                rt = rule.get("type")
                if isinstance(rt, str):
                    infl[rt] = rule

        replacement = None
        rule_id = None
        rule_type_out = None
        inflection_out = None

        word_val = first.get("word")
        direct = infl.get(word_val) if isinstance(word_val, str) else None
        if isinstance(direct, dict) and direct.get("word"):
            replacement = direct["word"]
            rule_id = direct.get("id")
        else:
            replacement_rule = None
            types = first.get("types", [])
            if isinstance(types, list):
                for part in types:
                    if part in infl:
                        replacement_rule = replacement_rule or infl[part]
            if isinstance(replacement_rule, dict):
                forms = first.get("inflections", {})
                inflection = replacement_rule.get("inflection")
                if isinstance(forms, dict) and isinstance(inflection, str):
                    replacement = forms.get(inflection) or first.get(
                        "word"
                    )
                    inflection_out = inflection
                else:
                    replacement = first.get("word")
                rule_id = replacement_rule.get("id")
                rule_type_out = inflection

        return replacement, rule_id, rule_type_out, inflection_out

    def _apply_joins(
        self,
        tokens: List[RenderedToken],
        join_rules: List[Dict[str, Any]],
    ) -> List[RenderedToken]:
        result: List[RenderedToken] = []
        i = 0
        while i < len(tokens):
            if result:
                prev_surface = result[-1].surface
                jr = _join_from_rules(
                    join_rules, prev_surface, tokens[i].surface
                )
                if jr and jr.replaces_pair:
                    merged = RenderedToken(
                        index=result[-1].index,
                        base=result[-1].base,
                        surface=jr.result,
                        join_applied=jr.rule_id,
                    )
                    result[-1] = merged
                    i += 1
                    continue
            result.append(tokens[i])
            i += 1
        return result

    @staticmethod
    def _compute_diffs(
        old: List[str], new: List[RenderedToken]
    ) -> List[RenderDiff]:
        diffs: List[RenderDiff] = []
        new_surfaces = [t.surface for t in new]
        max_len = max(len(old), len(new_surfaces))
        for i in range(max_len):
            old_s = old[i] if i < len(old) else None
            new_s = new_surfaces[i] if i < len(new_surfaces) else None
            if old_s is None and new_s is not None:
                diffs.append(
                    RenderDiff(
                        index=i, old_surface=None, new_surface=new_s,
                        kind="add",
                    )
                )
            elif old_s is not None and new_s is None:
                diffs.append(
                    RenderDiff(
                        index=i, old_surface=old_s, new_surface="",
                        kind="remove",
                    )
                )
            elif old_s != new_s:
                diffs.append(
                    RenderDiff(
                        index=i,
                        old_surface=old_s,
                        new_surface=new_s or "",
                        kind="change",
                    )
                )
        return diffs


def _join_from_rules(
    join_rules: List[Dict[str, Any]], prev: str, next_word: str
) -> Optional[JoinResult]:
    prev_lower = prev.lower()
    next_lower = next_word.lower()
    for rule in join_rules:
        if not isinstance(rule, dict):
            continue
        prev_list = rule.get("prev", [])
        if isinstance(prev_list, str):
            prev_list = [prev_list]
        if not isinstance(prev_list, list) or prev_lower not in [
            p.lower() if isinstance(p, str) else "" for p in prev_list
        ]:
            continue
        next_exact = rule.get("next")
        next_match = rule.get("next_match")
        matched = False
        if isinstance(next_exact, list):
            matched = next_lower in [
                n.lower() if isinstance(n, str) else "" for n in next_exact
            ]
        elif isinstance(next_exact, str):
            matched = next_lower == next_exact.lower()
        if not matched and isinstance(next_match, str):
            try:
                matched = bool(re.search(next_match, next_lower))
            except re.error:
                continue
        if not matched:
            continue
        result_template = rule.get("result", "{prev} {next}")
        result_str = (
            result_template.replace("{prev}", prev).replace(
                "{next}", next_word
            )
        )
        return JoinResult(
            result=result_str,
            rule_id=rule.get("id"),
            reason=rule.get("reason"),
            replaces_pair=result_template != "{prev} {next}",
        )
    return None


def create_buffer(
    locale: str,
    words_data: Optional[Dict[str, Any]] = None,
    rules_data: Optional[Dict[str, Any]] = None,
) -> SentenceBuffer:
    return SentenceBuffer(locale, words_data, rules_data)
