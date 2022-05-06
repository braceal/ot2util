import json
import yaml
import argparse
from pathlib import Path
from typing import Type, TypeVar, Union, Optional, List
from pydantic import BaseSettings as _BaseSettings

_T = TypeVar("_T")

PathLike = Union[str, Path]


class BaseSettings(_BaseSettings):
    def write_yaml(self, cfg_path: PathLike) -> None:
        with open(cfg_path, mode="w") as fp:
            yaml.dump(json.loads(self.json()), fp, indent=4, sort_keys=False)

    @classmethod
    def from_yaml(cls: Type[_T], filename: PathLike) -> _T:
        with open(filename) as fp:
            raw_data = yaml.safe_load(fp)
        return cls(**raw_data)  # type: ignore[call-arg]

    @classmethod
    def from_bytes(cls: Type[_T], raw_bytes: bytes) -> _T:
        raw_data = yaml.safe_load(raw_bytes)
        return cls(**raw_data)  # type: ignore[call-arg]


class LabwareConfig(BaseSettings):
    name: str
    location: str


class InstrumentConfig(BaseSettings):
    name: str
    mount: str


class OpentronsConfig(BaseSettings):
    # Remote setup parameters (None if running locally)
    # Remote directory path to stage experiments in
    remote_dir: Path
    # Remote host i.e. [user@]host
    host: str
    # Port to connect to OT-2 with
    port: int = 22
    # Private key path (defaults to ~/.ssh/id_rsa)
    key_filename: Optional[str] = None
    # Path to opentrons_simulate or opentrons_execute directory
    opentrons_path: Path = Path("/bin")
    # Whether or not to tar files before transferring from remote to local
    tar_transfer: bool = False


class ProtocolConfig(BaseSettings):
    # Path to write data to on the raspberry pi
    workdir: Path = Path("/root")


class ExperimentConfig(BaseSettings):
    # Connect to one (or many) OT-2s
    robots: List[OpentronsConfig] = []
    # Directory to write experimental results to
    output_dir: Path = Path()
    # Toggle simulation
    run_simulation: bool = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="YAML config file", type=str, required=True
    )
    args = parser.parse_args()
    return args
