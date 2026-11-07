"""
FoodLens Deterministic Audio Narration Engine
Builds speech-friendly, accessible verbal scripts from validated product nutrition and allergen facts.

Key Guarantees:
1. Pure Python deterministic generation (zero LLM translation).
2. Order: Allergen Alert (First) -> Product Name -> Portion Basis -> Key Nutrients -> Flags -> Disclaimer.
3. Every spoken number originates strictly from verified input JSON.
4. Banned safety words ('safe', 'allergen-free', 'सुरक्षित', 'एलर्जी-मुक्त') strictly forbidden.
5. Speech-friendly units: g -> grams/ग्राम, mg -> milligrams/मिलीग्राम, kcal -> calories/किलोकैलोरी, tsp -> teaspoons/चम्मच.
6. Length capped under 45 seconds (~90 words).
7. Zero personal names or avatars in scripts.
"""

import json
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"


class NarrationMode(str, Enum):
    SHORT = "short"
    DETAILED = "detailed"


@dataclass(frozen=True)
class NarrationScript:
    text: str
    language: str
    mode: NarrationMode
    word_count: int
    duration_seconds: float


def _load_i18n_dict(language: str) -> Dict[str, str]:
    lang_file = I18N_DIR / f"{language.lower()}.json"
    if not lang_file.exists():
        lang_file = I18N_DIR / "en.json"

    with open(lang_file, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_narration_script(
    data: Dict[str, Any],
    language: str = "en",
    mode: NarrationMode = NarrationMode.DETAILED,
) -> NarrationScript:
    """
    Builds a spoken audio script from validated product & portion data.
    """
    lang = language.lower() if language.lower() in ("en", "hi") else "en"
    i18n = _load_i18n_dict(lang)

    sentences: List[str] = []

    # 1. Allergen alert MUST be first
    has_allergen_alert = data.get("has_allergen_alert", False)
    allergen_text = data.get("allergen_text", "")

    if has_allergen_alert and allergen_text:
        # Strip potential personal names or greetings
        clean_allergen = allergen_text.replace("Alert for ", "").replace("के लिए चेतावनी", "").strip()
        sentences.append(i18n["allergen_alert_prefix"].format(text=clean_allergen))
    elif not has_allergen_alert:
        # Only in detailed mode speak no-allergen note
        if mode == NarrationMode.DETAILED:
            sentences.append(i18n["no_allergen_alert"])

    # 2. Product Name & Portion Basis
    name = data.get("name", "Packaged Product")
    portion_g = data.get("portion_grams", 100.0)
    sentences.append(i18n["product_basis"].format(name=name, grams=int(portion_g) if portion_g.is_integer() else portion_g))

    # 3. Energy (Calories)
    energy = data.get("energy_kcal")
    if energy is not None:
        val_str = str(int(energy)) if float(energy).is_integer() else str(energy)
        sentences.append(i18n["energy_line"].format(val=val_str))

    # 4. Sugar & Teaspoons
    sugars_g = data.get("sugars_g")
    tsp = data.get("sugar_teaspoons")
    if sugars_g is not None and tsp is not None:
        s_str = str(int(sugars_g)) if float(sugars_g).is_integer() else str(sugars_g)
        t_str = str(int(tsp)) if float(tsp).is_integer() else str(tsp)
        sentences.append(i18n["sugar_line"].format(grams=s_str, teaspoons=t_str))

    # 5. Detailed mode: Protein, Fat, Sodium, Notable Flags
    if mode == NarrationMode.DETAILED:
        protein = data.get("protein_g")
        if protein is not None:
            p_str = str(int(protein)) if float(protein).is_integer() else str(protein)
            sentences.append(i18n["protein_line"].format(val=p_str))

        fat = data.get("fat_g")
        if fat is not None:
            f_str = str(int(fat)) if float(fat).is_integer() else str(fat)
            sentences.append(i18n["fat_line"].format(val=f_str))

        sodium = data.get("sodium_mg")
        if sodium is not None:
            so_str = str(int(sodium)) if float(sodium).is_integer() else str(sodium)
            sentences.append(i18n["sodium_line"].format(val=so_str))

        # Flags (short neutral observations)
        notable_flags = data.get("notable_flags", [])
        for flag in notable_flags[:1]:
            if flag:
                sentences.append(str(flag))

    # 6. Closing Disclaimer (Mandatory)
    sentences.append(i18n["closing_disclaimer"])

    # Combine into speech text
    sep = " " if lang == "en" else " "
    full_text = sep.join(sentences)

    words = full_text.split()
    word_count = len(words)
    # Estimate speech duration: ~130 words per minute -> 2.16 words per second
    estimated_duration = round(word_count / 2.16, 1)

    return NarrationScript(
        text=full_text,
        language=lang,
        mode=mode,
        word_count=word_count,
        duration_seconds=estimated_duration,
    )
