from typing import List

from pebble import ProcessPool

from ot2util.config import BaseSettings, RobotConnectionConfig, parse_args
from ot2util.experiment import RobotConnection


def configure_ot2(
    connection: RobotConnectionConfig,
    update_package: bool = True,
    update_calibration: bool = False,
    commands: List[str] = [],
) -> None:
    """Configure a single OT-2 remotely."""
    conn = RobotConnection(**connection.dict())

    if update_package:
        conn.run("git clone https://github.com/braceal/ot2util.git")
        conn.run("pip install -r ot2util/requirements/ot2-minimal.txt")
        conn.run("pip install ot2util/")

    if update_calibration:
        conn.run("mv .opentrons/ .opentrons-back")
        conn.run("cp -r /var/data/* ~/.opentrons/")

    for command in commands:
        conn.run(command)


def configure_ot2s(
    connections: List[RobotConnectionConfig],
    update_package: bool = True,
    update_calibration: bool = False,
    commands: List[str] = [],
) -> None:
    """Configure many OT-2s remotely."""
    with ProcessPool(max_workers=len(connections)) as pool:
        for connection in connections:
            pool.schedule(
                function=configure_ot2,
                args=(connection, update_package, update_calibration, commands),
            )
        pool.close()
        pool.join()


class OpentronsInstallationConfig(BaseSettings):
    """Configuration for installing ot2util across many OT-2s"""

    connections: List[RobotConnectionConfig] = []
    """Configuration for connecting to the robot via ssh."""
    update_package: bool = True
    """Whether or not to update the ot2util package."""
    update_calibration: bool = False
    """Whether or not to update the calibration files."""
    commands: List[str] = []
    """List of extra commands to run."""


if __name__ == "__main__":
    args = parse_args()
    cfg = OpentronsInstallationConfig.from_yaml(args.config)
    configure_ot2s(**cfg.dict())
