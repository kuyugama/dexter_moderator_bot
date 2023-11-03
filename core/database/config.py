from pathlib import Path
from configparser import ConfigParser

from .. import config

reader = ConfigParser()
reader.read(Path(__file__).parent / "config.ini")

section = "database.prod"
if config.mode == "test":
    section = "database.test"

DB_NAME = reader.get(section, "name")
DB_USERNAME = reader.get(section, "username")
DB_ADDRESS = reader.get(section, "address")
DB_PASSWORD = reader.get(section, "password")
DB_PORT = reader.get(section, "port")

REDIS_USERNAME = reader.get("redis", "username")
REDIS_PASSWORD = reader.get("redis", "password")
REDIS_ADDRESS = reader.get("redis", "address")
REDIS_PORT = reader.get("redis", "port")
REDIS_DB = reader.get("redis", "db")
