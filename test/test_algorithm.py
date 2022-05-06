def test_algorithm_init():
    from ot2util.config import ExperimentConfig
    from ot2util.algorithm import Algorithm

    cfg = ExperimentConfig()
    algorithm = Algorithm(cfg)
    correct = "Algorithm(robots=[] output_dir=PosixPath('.') run_simulation=True)"
    assert str(algorithm) == correct
