import json
from pathlib import Path
from configparser import ConfigParser

reader = ConfigParser()
reader.read(Path(__file__).parent / "config.ini")

mode = reader.get("application", "mode")

administrators = json.loads(reader.get("application", "administrators"))

section = "bot.prod"
if mode == "test":
    section = "bot.test"

BOT_TOKEN = reader.get(section, "token")
