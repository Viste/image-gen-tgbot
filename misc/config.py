import configparser
from dataclasses import dataclass

@dataclass
class Nasty:
    token: str
    api_key: str
    api_url: str
    admins_id: int
    channel: int

@dataclass
class Config:
    main: Nasty

def load_config(path: str):
    config = configparser.ConfigParser()
    config.read(path)

    main = config["main"]

    return Config(
        main=Nasty(
            token=main.get("token"),
            api_key=main.get("api_key"),
            api_url=main.get("api_url"),
            admins_id=main.getint("admins_id"),
            channel=main.getint("channel"),
        ),
    )
