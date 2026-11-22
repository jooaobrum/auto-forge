"""Loads config/project.yml and resolves the environment's write target."""
import pathlib
import yaml

def load(env, path="config/project.yml"):
    cfg = yaml.safe_load(pathlib.Path(path).read_text())
    e = cfg["environments"][env]
    cfg["env"] = env
    cfg["target"] = f"{e['catalog']}.{e['schema']}"
    return cfg
