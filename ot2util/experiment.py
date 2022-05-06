import time
import subprocess
from typing import Optional, Union, List
from pathlib import Path
from fabric import Connection
from invoke.runners import Result
from ot2util.config import ProtocolConfig, OpentronsConfig, PathLike


def _write_log(contents: Union[str, bytes], path: Path) -> None:
    mode = "wb" if isinstance(contents, bytes) else "w"
    with open(path, mode) as f:
        f.write(contents)


class Experiment:
    """Encapsulation of a singular experiment.

    Contains information local to a singular protocol. Will be executed by experiment manager
    """

    def __init__(
        self,
        name: str,
        output_dir: PathLike,
        protocol: PathLike,
        cfg: ProtocolConfig,
    ) -> None:
        self.name = name
        self.output_dir = Path(output_dir) / name
        self.protocol = Path(protocol)
        self.yaml = self.output_dir / "config.yaml"
        self.cfg = cfg

        # Create new experiment directory
        self.output_dir.mkdir()


class Opentrons:
    """Manage a set of experiments to be run in the same session."""

    def __init__(
        self,
        run_simulation: bool,
        remote_dir: PathLike,
        host: Optional[str] = None,
        port: int = 22,
        key_filename: Optional[str] = None,
        opentrons_path: PathLike = Path("/bin"),
        tar_transfer: bool = False,
    ) -> None:
        """Initialize a new connection to an Opentrons.

        Parameters
        ----------
        run_simulation : bool
            If True, runs opentrons_simulate instead of opentrons_execute.
        remote_dir : Path
            Path on the opentrons to write intermediate experiment results
            and configuration files to.
        host : Optional[str], optional
            If specified will connect to the opentrons raspberry pi over
            ssh and allow jobs to be run remotely. To specify :obj:`host`
            use the following format [user@]host. For example, "deploy@web1".
        key_filename : Optional[str], optional
            If :obj:`host` is specified, a path to your private key file
            must be supplied to the Fabric Connection. For example,
            "/home/myuser/.ssh/private.key".
        opentrons_path : Optional[str], optional
            Path to directory containing the opentrons_simulate and
            opentrons_execute commands.
        tar_transfer : bool, optional
            Whether or not to tar files before transferring from the
            raspberry pi to local. Note that this will slow down communcation
            but may be necessary if transferring large files, by default, False.
        """
        opentrons_exe = "opentrons_simulate" if run_simulation else "opentrons_execute"
        self.exe = Path(opentrons_path) / opentrons_exe
        self.remote_dir = Path(remote_dir)
        self.host = host
        self.key_filename = key_filename
        self.tar_transfer = tar_transfer
        # Whether or not an experiment is currently running on this connection
        self.running = False

        self.conn = None
        if host is not None:
            connect_kwargs = {}
            if key_filename is not None:
                connect_kwargs["key_filename"] = [key_filename]

            # TODO: Handle authentication in a better way
            self.conn = Connection(host=host, port=port, connect_kwargs=connect_kwargs)
            # Make staging directory on the Opentrons
            self.conn.run(f"mkdir -p {self.remote_dir}")
            # TODO: We may be able to add an optional proxy jump to connect
            #       to the robot from a remote location not connected to the
            #       robots local WiFi environment.
            # https://docs.fabfile.org/en/2.6/concepts/networking.html#proxyjump

    def __del__(self) -> None:
        # Close the remote connection
        if self.conn is not None:
            self.conn.close()

    def _scp(self, src: PathLike, dst: PathLike, recursive: bool = False) -> None:
        r = "-r" if recursive else ""
        identity_file = "" if self.key_filename is None else f"-i {self.key_filename}"
        subprocess.run(f"scp {identity_file} {r} {src} {dst}", shell=True)

    def _tar_transfer(
        self, experiment: Experiment, workdir: Path, remote_protocol: Path
    ) -> None:
        assert self.conn is not None
        local_tmp = experiment.output_dir / experiment.name
        remote_tar = workdir.parent / f"{experiment.name}.tar.gz"
        local_tar = str(experiment.output_dir / remote_tar.name)
        excludes = f'--exclude="{remote_protocol.name}"'
        tar_command = f"tar {excludes} -cvf {remote_tar} {workdir.name}"
        self.conn.run(f"cd {workdir.parent} && {tar_command}")
        self._scp(f"{self.host}:{remote_tar}", local_tar)

        # Clean up the tar on remote
        self.conn.run(f"rm -r {remote_tar}")

        # Extract payload into experiment output directory and clean up transfer files
        subprocess.run(f"tar -xf {local_tar} -C {experiment.output_dir}", shell=True)
        subprocess.run(f"mv {local_tmp}/* {experiment.output_dir}", shell=True)
        subprocess.run(f"rm -r {local_tmp} {local_tar}", shell=True)

    def _scp_transfer(
        self, experiment: Experiment, workdir: Path, remote_protocol: Path
    ) -> None:
        # TODO: Try rsync to exclude the remote_protocol files
        # https://www.cyberciti.biz/faq/scp-exclude-files-when-using-command-recursively-on-unix-linux/
        # https://stackoverflow.com/questions/1228466/how-to-filter-files-when-using-scp-to-copy-dir-recursively
        to_copy = f"{self.host}:{workdir / '*'}"
        self._scp(to_copy, experiment.output_dir, recursive=True)

    def _transfer(
        self, experiment: Experiment, workdir: Path, remote_protocol: Path
    ) -> None:
        if self.tar_transfer:
            self._tar_transfer(experiment, workdir, remote_protocol)
        else:
            self._scp_transfer(experiment, workdir, remote_protocol)

    def _run_remote(self, experiment: Experiment) -> int:
        assert self.conn is not None

        # /root/test1/experiment-1
        workdir = experiment.cfg.workdir = self.remote_dir / experiment.name
        # Write a yaml protocol configuration to local
        experiment.cfg.write_yaml(experiment.yaml)

        # Adjust paths to remote workdir
        remote_protocol = workdir / experiment.protocol.name
        # TODO: It would be cleaner if remote_yaml was stored in workdir
        #       but there is a bug in the opentrons code that does not
        #       propogate the -d argument used to pass the config file
        #       to the protocol. See protocol.py for more explanation.
        remote_yaml = workdir.parent / experiment.yaml.name

        # Transfer protocol file and configuration over to remote
        self.conn.run(f"mkdir -p {workdir}")
        self._scp(experiment.protocol, f"{self.host}:{remote_protocol}")
        self._scp(experiment.yaml, f"{self.host}:{remote_yaml}")

        # Execute remote experiment
        result: Result = self.conn.run(f"{self.exe} {remote_protocol}")
        _write_log(result.stdout, experiment.output_dir / "stdout.log")
        _write_log(result.stderr, experiment.output_dir / "stderr.log")
        returncode: int = result.exited
        if returncode != 0:
            # Return early since something went wrong
            return returncode

        # Transfer experiment results back to local
        self._transfer(experiment, workdir, remote_protocol)

        # Clean up experiment on remote
        self.conn.run(f"rm -r {workdir} {remote_yaml}")

        return returncode

    def run(self, experiment: Experiment) -> int:
        self.running = True
        returncode = self._run_remote(experiment)
        self.running = False
        return returncode


class ExperimentManager:
    def __init__(self, run_simulation: bool, robots: List[OpentronsConfig]) -> None:

        if not run_simulation and not robots:
            raise ValueError("robots must be specified if run_simulation is False")

        self.robots = [
            Opentrons(
                run_simulation,
                r.remote_dir,
                r.host,
                r.port,
                r.key_filename,
                r.opentrons_path,
                r.tar_transfer,
            )
            for r in robots
        ]

    def _get_robot(self) -> Opentrons:
        while True:
            for robot in self.robots:
                if not robot.running:
                    return robot
            time.sleep(30)  # Wait 30 seconds and try again

    def _run_remote(self, experiment: Experiment) -> int:
        robot = self._get_robot()
        return robot.run(experiment)

    def _run_local(self, experiment: Experiment) -> int:
        # In the case of local runs, set the workdir to the output directory
        experiment.cfg.workdir = experiment.output_dir
        # Write a yaml protocol configuration to local
        experiment.cfg.write_yaml(experiment.yaml)
        # The -d option corresponds to the opentrons custom-data-file argument
        # which passes the config file to the protocol.bundled_data field
        command = f"opentrons_simulate {experiment.protocol} -d {experiment.yaml}"
        proc = subprocess.run(command, shell=True, capture_output=True)
        _write_log(proc.stdout, experiment.output_dir / "stdout.log")
        _write_log(proc.stderr, experiment.output_dir / "stderr.log")
        return proc.returncode

    def run(self, experiment: Experiment) -> int:
        """Execute an experiment object.

        Will execute an experiment according to the paramters of the experiment.
        Can determine to run locally or on the OT2.

        Parameters
        ----------
        experiment : Experiment
            Protocol to be run. Contains necesary information to run trial.

        Returns
        -------
        int
            Return code of experiment. 0 is success, anything other than 0 is a failure
        """
        if self.robots:
            return self._run_remote(experiment)
        return self._run_local(experiment)
