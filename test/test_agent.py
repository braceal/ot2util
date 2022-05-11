def test_agent_init():
    from ot2util.config import ExperimentConfig
    from ot2util.agent import Agent

    cfg = ExperimentConfig()
    agent = Agent(cfg)
    correct = "Agent(robots=[] output_dir=PosixPath('.') run_simulation=True)"
    assert str(agent) == correct
