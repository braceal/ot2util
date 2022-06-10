"""Utility for automatically installing the package software
on many OT-2's at the same time."""
from pathlib import Path
from typing import List

from pebble import ProcessPool

from ot2util.utils import write_file
from ot2util.config import BaseSettings, RobotConnectionConfig, parse_args
from ot2util.experiment import RobotConnection


def configure_ot2(
    connection: RobotConnectionConfig,
    branch: str = "main",
    update_package: bool = True,
    update_calibration: bool = False,
    commands: List[str] = [],
    log_dir: Path = Path("."),
) -> None:
    """Configure a single OT-2 remotely."""
    conn = RobotConnection(**connection.dict())
    stdout, stderr = [], []

    def _run(command: str) -> None:
        result = conn.run(command)
        if result.return_code != 0:
            logs = f"{result.stdout}\n{result.stderr}"
            raise ValueError(f"Error on connection {conn}\n{command}\n{logs}")
        stdout.append(result.stdout)
        stderr.append(result.stderr)

    if update_package:
        _run("rm -rf ot2util/")
        _run(f"git clone -b {branch} https://github.com/braceal/ot2util.git")
        _run("pip install -r ot2util/requirements/ot2-minimal.txt")
        _run("pip install ot2util/")

    if update_calibration:
        _run("mv .opentrons/ .opentrons-back")
        _run("cp -r /var/data/* ~/.opentrons/")

    for command in commands:
        _run(command)

    write_file("\n".join(stdout), log_dir / f"{conn}.stdout")
    write_file("\n".join(stderr), log_dir / f"{conn}.stderr")


def configure_ot2s(
    connections: List[RobotConnectionConfig],
    branch: str = "main",
    update_package: bool = True,
    update_calibration: bool = False,
    commands: List[str] = [],
    log_dir: Path = Path("."),
) -> None:
    """Configure many OT-2s remotely."""
    log_dir.mkdir(exist_ok=True)
    # TODO: Fix bug
    # with ProcessPool(max_workers=len(connections)) as pool:
    #     for connection in connections:
    #         pool.schedule(
    #             function=configure_ot2,
    #             args=(
    #                 connection,
    #                 branch,
    #                 update_package,
    #                 update_calibration,
    #                 commands,
    #                 log_dir,
    #             ),
    #         )

    # Run serial for debugging
    for connection in connections:
        configure_ot2(
            connection,
            branch,
            update_package,
            update_calibration,
            commands,
            log_dir,
        )

    print("Done")


class OpentronsInstallationConfig(BaseSettings):
    """Configuration for installing ot2util across many OT-2s"""

    # TODO: Swtich all lists to a default list factory
    connections: List[RobotConnectionConfig] = []
    """Configuration for connecting to the robot via ssh."""
    branch: str = "main"
    """Specific branch of repository to install (defaults to main)."""
    update_package: bool = True
    """Whether or not to update the ot2util package."""
    update_calibration: bool = False
    """Whether or not to update the calibration files."""
    commands: List[str] = []
    """List of extra commands to run."""
    log_dir: Path = Path(".")
    """Directory to write logs to."""


if __name__ == "__main__":
    args = parse_args()
    config = OpentronsInstallationConfig.from_yaml(args.config)
    print(config)
    configure_ot2s(**config.dict())
