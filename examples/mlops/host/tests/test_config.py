from churn import config


def test_each_environment_writes_to_its_own_schema():
    targets = {env: config.load(env)["target"] for env in ("dev", "qa", "prod")}
    assert len(set(targets.values())) == 3
    assert config.load("dev")["model"]["threshold"] == 0.5
