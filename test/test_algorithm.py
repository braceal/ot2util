def test_agent_init():
    from ot2util.agent import Agent
    from ot2util.config import WorkflowConfig

    cfg = WorkflowConfig()
    agent = Agent(cfg)
    correct = "Agent(robots=[] output_dir=PosixPath('.'))"
    assert str(agent) == correct
