"""Settings for specific configurations of OT2 machines and experiments."""
import argparse
import json
from pathlib import Path
from typing import List, Optional, Type, TypeVar, Union

import yaml
from opentrons.protocol_api import ProtocolContext
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

    @classmethod
    def get_config(cls: Type[_T], protocol: ProtocolContext) -> _T:
        """Load configuration file when running an opentrons protocol."""
        # https://github.com/Opentrons/opentrons/blob/edge/api/src/opentrons/util/entrypoint_util.py#L59
        # protocol.bundled_data["config.yaml"] will contain the raw bytes of the config file
        # TODO: There is a bug in the opentrons code which does not pass this parameter
        #       correctly during opentrons_execute commands.
        if "config.yaml" in protocol.bundled_data:
            return cls.from_bytes(protocol.bundled_data["config.yaml"])  # type: ignore
        # As a quick fix, we hard code a path to write config files to.
        remote_dir = Path("/root/test1")
        return cls.from_yaml(remote_dir / "config.yaml")  # type: ignore


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


class RobotConnectionConfig(BaseSettings):
    remote_dir: Path
    """Path of directory to store results on the robot,
    will be removed at end of experiment"""
    host: str
    """Host information of the robot, i.e `[user@]host`."""
    port: int = 22
    """Port to connect to robot, unless otherwise specified, use normal ssh port (22)."""
    key_filename: Optional[str] = None
    """Path to your private ssh-key, refer to OT2 documentation for setup
    (defaults to ~/.ssh/id_rsa)."""
    tar_transfer: bool = False
    """Compress files for transfering from remote to local,
    slow operation, avoid if possible."""


class MetaDataConfig(BaseSettings):
    """Configuration for specifying Opentrons metadata."""

    protocolName: str = "My Protocol"
    author: str = "Name <email@address.com>"
    description: str = "Simple protocol to get started using OT2"
    apiLevel: str = "2.12"


class ProtocolConfig(BaseSettings):
    """Basic configuration for running a protocol."""

    workdir: Path = Path("/root")
    """Workdir for the experiment running on remote."""


class RobotConfig(BaseSettings):
    """Configuration for using a robot."""

    connection: Optional[RobotConnectionConfig] = None
    """Configuration for connecting to the robot via ssh."""


class OpentronsRobotConfig(RobotConfig):
    """Configuration for using and Opentrons robot."""

    metadata: MetaDataConfig = MetaDataConfig()
    """Opentrons metadata to specify in the protocol."""
    opentrons_path: Path = Path("/bin")
    """Path to opentrons_simulate or opentrons_execute directory."""
    run_simulation: bool = False
    """Whether or not to run a simulation or an actual experiment"""
    run_local: bool = False
    """Whether or not to run the local in simulated mode"""


class WorkflowConfig(BaseSettings):
    """Configuration for specifiying an experimental workflow."""

    robots: List[RobotConfig] = []
    """Robots available to run experiments on. Connect to one or many."""
    output_dir: Path = Path()
    """Local directory to pull results into from the remote experiments"""


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
    >>> cfg = WorkflowConfig.from_yaml(args.config)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="YAML config file", type=str, required=True
    )
    args = parser.parse_args()
    return args
