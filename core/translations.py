import os
from pathlib import Path

from yaml import load, FullLoader, dump, Dumper

translations_dir = Path(__file__).parent / "translations"

translations_files = os.listdir(str(translations_dir.absolute()))


translations = {
    "languages": {}
}

for file in translations_files:
    if not file.endswith(".yml"):
        continue
    file_path = translations_dir / file

    with open(file_path, encoding="utf8") as f:
        translation = load(f, FullLoader)

    if "code" not in translation:
        continue

    if "name" not in translation:
        continue

    translations["languages"][translation["code"]] = translation["name"]

    translations[translation["code"]] = translation


def get_languages():
    return translations["languages"]


def get(path: str, language="en"):
    base = translations[language]

    for key in path.split("."):
        if key not in base:
            return f"{path} not found in language: {language}"
        base = base[key]

    return base


def get_string(path, language="en"):
    base = translations[language]
    for key in path.split("."):
        if key not in base:
            return f"{path} not found in language: {language}"
        base = base[key]

    return base


def get_string_by_list(*path, language="en"):
    base = translations[language]
    for key in path:
        if key not in base:
            return f"{path} not found in language: {language}"
        base = base[key]

    return base


def add_string(path, string, language="en"):
    base = translations[language]

    for key in path.split(".")[:-1]:
        if key not in base:
            base[key] = {}
            base = base[key]
            continue
        base = base[key]

    base[path.split(".")[-1]] = string

    with open("translations.yml", "w", encoding="utf8") as f:
        dump(translations, f, Dumper, allow_unicode=True)
