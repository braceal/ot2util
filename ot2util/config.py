import json
import yaml
import argparse
from pathlib import Path
from typing import Type, TypeVar, Union
from pydantic import BaseSettings as _BaseSettings

_T = TypeVar("_T")

PathLike = Union[str, Path]


class BaseSettings(_BaseSettings):
    """Allows any sub-class to inherit methods allowing for programatic description of protocols

    Can load a yaml into a class and dump a class into a yaml file. 

    
    """
    def dump_yaml(self, cfg_path: PathLike) -> None:
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


class ProtocolConfig(BaseSettings):
    """Basic configuration for running a protocol

    """
    # Path to write data to on the raspberry pi
    workdir: Path = Path.home()


class LabwareConfig(BaseSettings):
    """Configuration for the labware in the deck of OT2

    """
    name: str
    location: str


class InstrumentConfig(BaseSettings):
    """Configuration dataclass for the OT2 head module

    """
    name: str
    mount: str


def parse_args() -> argparse.Namespace:
    """Parses command line arguments using argparse library 

    Returns:
        argparse.Namespace: dict like object with parsed command line inputs
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="YAML config file", type=str, required=True
    )
    args = parser.parse_args()
    return args
