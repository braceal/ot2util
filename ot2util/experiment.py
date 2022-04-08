import subprocess
from pathlib import Path
from ot2util.config import BaseSettings, PathLike


class Experiment:
    def __init__(
        self,
        name: str,
        output_dir: PathLike,
        protocol_script_path: PathLike,
        protocol_cfg: BaseSettings,
    ):
        self.outdir = Path(output_dir) / name
        self.yaml = self.outdir / "config.yaml"
        self.protocol_script_path = protocol_script_path

        # Create new experiment directory
        self.outdir.mkdir()
        protocol_cfg.dump_yaml(self.yaml)


class ExperimentManager:
    def __init__(self, run_simulation: bool):
        self.exe = "opentrons_simulate" if run_simulation else "opentrons_execute"

    def run(self, experiment: Experiment) -> int:
        # The -d option corresponds to the opentrons custom-data-file argument
        # which passes the config file to the protocol.bundled_data field
        command = f"{self.exe} {experiment.protocol_script_path} -d {experiment.yaml}"
        proc = subprocess.run(command, shell=True, capture_output=True)
        with open(experiment.outdir / "stdout.log", "wb") as f:
            f.write(proc.stdout)
        with open(experiment.outdir / "stderr.log", "wb") as f:
            f.write(proc.stderr)
        return proc.returncode
