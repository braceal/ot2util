"""Settings for specific configurations of OT2 machines and experiments.
"""
import json
import yaml
import argparse
from pathlib import Path
from typing import Type, TypeVar, Union, Optional, List
from pydantic import BaseSettings as _BaseSettings

_T = TypeVar("_T")

PathLike = Union[str, Path]


class BaseSettings(_BaseSettings):
    """Allows any sub-class to inherit methods allowing for programatic description of protocols

    Can load a yaml into a class and write a class into a yaml file.
    """

    def write_yaml(self, cfg_path: PathLike) -> None:
        """Allows programatic creation of ot2util objects and saving them into yaml.

        Parameters
        ----------
        cfg_path : PathLike
            Path to dump the yaml file.
        """
        with open(cfg_path, mode="w") as fp:
            yaml.dump(json.loads(self.json()), fp, indent=4, sort_keys=False)

    @classmethod
    def from_yaml(cls: Type[_T], filename: PathLike) -> _T:
        """Allows loading of yaml into ot2util objects.

        Parameters
        ----------
        filename: PathLike
            Path to yaml file location.
        """
        with open(filename) as fp:
            raw_data = yaml.safe_load(fp)
        return cls(**raw_data)  # type: ignore[call-arg]

    @classmethod
    def from_bytes(cls: Type[_T], raw_bytes: bytes) -> _T:
        """Allows ot2util objects to be built after being sent over network."""
        raw_data = yaml.safe_load(raw_bytes)
        return cls(**raw_data)  # type: ignore[call-arg]


class LabwareConfig(BaseSettings):
    """Configuration for the labware in the deck of OT2"""

    name: str
    """Name of labware corresponding to official OT2 naming"""
    location: str
    """Location in OT2, string of numbered location"""


class InstrumentConfig(BaseSettings):
    """Configuration dataclass for the OT2 head module"""

    name: str
    """Name of pipette tip installed in OT2, must correspond to official OT2 naming"""
    mount: str
    """Location, either `'right', 'left'`"""


class OpentronsConfig(BaseSettings):
    # Remote setup parameters (None if running locally)
    # Remote directory path to stage experiments in
    remote_dir: Path
    """Path of directory to store results on OT2, will be removed at end of experiment"""
    # Remote host i.e. [user@]host
    host: str
    """Host information of OT2 robot, i.e `[user@]host`"""
    # Port to connect to OT-2 with
    port: int = 22
    """Port to connect to OT2, unless otherwise specified, use normal ssh port (22)"""
    # Private key path (defaults to ~/.ssh/id_rsa)
    key_filename: Optional[str] = None
    """Path to your OT2 ssh-key, refer to OT2 documentation for setup"""
    # Path to opentrons_simulate or opentrons_execute directory
    opentrons_path: Path = Path("/bin")
    """Path to `opentrons` program executable """
    # Whether or not to tar files before transferring from remote to local
    tar_transfer: bool = False
    """Compress files for transfering, slow operation, avoid if possible"""


class ProtocolConfig(BaseSettings):
    """Basic configuration for running a protocol."""

    # Path to write data to on the raspberry pi
    workdir: Path = Path("/root")
    """Workdir for the raspberry pi in the OT2"""


class ExperimentConfig(BaseSettings):
    # Connect to one (or many) OT-2s
    robots: List[OpentronsConfig] = []
    """Robots available to run experiments on"""
    # Directory to write experimental results to
    output_dir: Path = Path()
    """Local directory to pull results into from the OT2 experiments"""
    # Toggle simulation
    run_simulation: bool = True
    """Whether or not to run a simulation or an actual experiment"""


def parse_args() -> argparse.Namespace:
    """Parses command line arguments using argparse library

    Returns
    -------
        argparse.Namespace:
            Dict like object containing a path to a YAML file
            accessed via the config property.

    Example
    -------
    >>> from ot2util.config import parse_args
    >>> args = parse_args()
    >>> cfg = ExperimentConfig.from_yaml(args.config)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="YAML config file", type=str, required=True
    )
    args = parser.parse_args()
    return args
