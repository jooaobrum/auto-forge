import argparse
from poc_secom import config

def main(argv=None, spark=None):
    p = argparse.ArgumentParser()
    p.add_argument("--env", choices=["dev", "qa", "prod"], required=True)
    cfg = config.load(p.parse_args(argv).env)
    ...  # train: calls functions of poc_secom with values from cfg
