"""Encapsulation of experiments allowing specification of arbitrary protocols to be run on OT2.
"""

import inspect
import logging
import subprocess
import time
from concurrent.futures import Future, wait
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, Union

import black
import pebble
from fabric import Connection
from invoke.runners import Result
from jinja2 import Environment, PackageLoader

from ot2util.config import (
    MetaDataConfig,
    OpentronsRobotConfig,
    PathLike,
    ProtocolConfig,
    RobotConnectionConfig,
)

logger = logging.getLogger(__name__)


def _getsource(func: Callable[..., Any]) -> str:
    code = inspect.getsource(func)
    lines = code.split("\n")
    indent = len(lines[0]) - len(lines[0].lstrip())
    lines = [line[indent:] for line in lines]
    code = "\n".join(lines)
    return code


def get_function_source_codes(funcs: List[Callable[..., Any]]) -> List[str]:
    source_codes = [_getsource(func) for func in funcs]
    return source_codes


def to_template(
    imports: Callable[[], None],
    config_class: ProtocolConfig,
    run_func: Callable[..., None],
    metadata: MetaDataConfig,
    funcs: List[Callable[..., Any]] = [],
    template_file: str = "protocol.j2",
) -> str:
    function_codes = get_function_source_codes(funcs + [run_func])
    context = {
        "imports": _getsource(imports),
        "config_code": inspect.getsource(config_class),  # type: ignore[arg-type]
        "metadata": metadata,
        "function_codes": function_codes,
    }
    env = Environment(
        loader=PackageLoader("ot2util"),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    template = env.get_template(template_file)
    return template.render(context)


def write_template(filename: Path, *args: Any, **kwargs: Any) -> None:
    source_code = to_template(*args, **kwargs)
    source_code = black.format_str(source_code, mode=black.FileMode(line_length=100))
    with open(filename, "w") as f:
        f.write(source_code)


def _write_log(contents: Union[str, bytes], path: Path) -> None:
    mode = "wb" if isinstance(contents, bytes) else "w"
    with open(path, mode) as f:
        f.write(contents)


class Experiment:
    """Encapsulation of a singular experiment.

    Contains information local to a singular protocol.
    Will be executed by experiment manager
    """

    def __init__(self, name: str, output_dir: PathLike, cfg: ProtocolConfig) -> None:
        self.name = name
        self.output_dir = Path(output_dir) / name
        self.protocol = self.output_dir / "protocol.py"
        self.yaml = self.output_dir / "config.yaml"
        self.cfg = cfg

        # Create new experiment directory
        self.output_dir.mkdir()

        self.returncode: int = -1

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, retcode={self.returncode})"


class RobotConnection:
    """Provide an ssh connection to issue remote commands to a robot."""

    def __init__(
        self,
        remote_dir: PathLike,
        host: str,
        port: int = 22,
        key_filename: Optional[str] = None,
        tar_transfer: bool = False,
    ) -> None:
        """Initialize a new connection to a robot.

        Parameters
        ----------
        remote_dir : Path
            Path on the opentrons to write intermediate experiment results
            and configuration files to.
        host : str
            If specified will connect to the opentrons raspberry pi over
            ssh and allow jobs to be run remotely. To specify :obj:`host`
            use the following format [user@]host. For example, "deploy@web1".
        key_filename : Optional[str], optional
            If :obj:`host` is specified, a path to your private key file
            must be supplied to the Fabric Connection. For example,
            "/home/myuser/.ssh/private.key".
        tar_transfer : bool, optional
            Whether or not to tar files before transferring from the
            raspberry pi to local. Note that this will slow down communcation
            but may be necessary if transferring large files, by default, False.
        """
        self.remote_dir = Path(remote_dir)
        self.host = host
        self.key_filename = key_filename
        self.tar_transfer = tar_transfer

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
        self.conn.close()

    def _scp(self, src: PathLike, dst: PathLike, recursive: bool = False) -> None:
        r = "-r" if recursive else ""
        identity_file = "" if self.key_filename is None else f"-i {self.key_filename}"
        subprocess.run(f"scp {identity_file} {r} {src} {dst}", shell=True)

    def _tar_transfer(
        self, experiment: Experiment, workdir: Path, remote_protocol: Path
    ) -> None:
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

    def run(self, command: str) -> Result:
        """Run command on remote shell.

        Parameters
        ----------
        command : str
            The command to run.

        Returns
        -------
        invoke.runners.Result
            A container for information about the result of a command execution.
        """
        return self.conn.run(command)


class Robot:
    protocol_config_class: ProtocolConfig = ProtocolConfig()

    def __init__(
        self,
        run_local: bool = False,
        connection: Optional[RobotConnectionConfig] = None,
    ) -> None:
        """_summary_

        Parameters
        ----------
        run_local : bool
            Whether or not to run a simulation or execute real experiment.
        connection : Optional[RobotConnectionConfig], optional
            Configuration to connect to robot via via ssh.
        """

        self._run_local = run_local
        # Initialize ssh connection to robot
        self.conn = None
        if connection is not None:
            self.conn = RobotConnection(**connection.dict())

        # Whether or not an experiment is currently running on this robot
        self.running = False

    def run_experiment(self, experiment: Experiment) -> int:
        if self._run_local:
            return self.run_local(experiment)
        return self.run_remote(experiment)

    def run_remote(self, experiment: Experiment) -> int:
        raise NotImplementedError

    def run_local(self, experiment: Experiment) -> int:
        raise NotImplementedError

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Implement protocol here."""
        raise NotImplementedError

    def setup_experiment(self, name: str, *args: Any, **kwargs: Any) -> Experiment:
        raise NotImplementedError

    def pre_experiment(self, experiment: Experiment, *args: Any, **kwargs: Any) -> None:
        return None

    def post_experiment(
        self, experiment: Experiment, *args: Any, **kwargs: Any
    ) -> None:
        return None


class RobotPool:
    """Class to manage experiments to be run. Will handle distributing
    protocols and running them on any/all OT2's available."""

    def __init__(self, robots: List[Robot], synchronized: bool = True) -> None:
        """Initialize the experiment manager with required environmental information.

        Parameters
        ----------
        robots : List[Robots]
            List of robots available.
        synchronized: bool
            If True, will block the calling thread if submitted jobs
            exceed the number of available robots (defaults to True).
        """
        self.robots = robots
        self.synchronized = synchronized
        self.futures: Set[Future[Experiment]] = set()
        self.pool = pebble.ThreadPool(max_workers=len(self.robots))

    def __del__(self) -> None:
        self.pool.close()
        self.pool.join()

    def _block_on_batch(self) -> None:
        """Wait for running experiments to finish if there are
        no more available robots."""
        if len(self.futures) == len(self.robots):
            for future in self.futures:
                future.result()
            self.futures = set()

    def submit(self, name: str, *args: Any, **kwargs: Any) -> Future[Experiment]:
        if self.synchronized:
            self._block_on_batch()

        future: Future[Experiment] = self.pool.schedule(
            self._run, args=(name, *args), kwargs=kwargs
        )
        self.futures.add(future)

        if len(self.robots) == 1:
            # wait returns a named tuple of futures wait().done is
            # a set of completed futures and since we only have a single
            # thread in this case, it will have one element so we pop it
            # from the set and return the Future.
            return wait([future]).done.pop()
        return future

    @pebble.synchronized  # type: ignore[misc]
    def _get_robot(self) -> Robot:
        while True:
            for robot in self.robots:
                if not robot.running:
                    robot.running = True
                    return robot
            if not robot.run_local:
                time.sleep(10)  # Wait 10 seconds and try again

    def _run(self, name: str, *args: Any, **kwargs: Any) -> Experiment:
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
        # Get a robot if one is available, or block.
        robot = self._get_robot()

        # Define the experiment to run
        experiment: Experiment = robot.setup_experiment(name, *args, **kwargs)

        # Run any pre-execution steps
        robot.pre_experiment(experiment, *args, **kwargs)

        # Run the experiment
        returncode = robot.run_experiment(experiment)

        # TODO: This should probably be checked elsewhere
        if returncode != 0:
            raise ValueError(
                f"Experiment {experiment.name} exited with returncode: {returncode}"
            )

        experiment.returncode = returncode

        # If experiment was successful, run post-execution steps
        robot.post_experiment(experiment, *args, **kwargs)

        # Free robot for next experiment
        robot.running = False

        return experiment


class OpenTronsRobot(Robot):
    def __init__(self, config: OpentronsRobotConfig):
        super().__init__(config.run_local, config.connection)

        self.metadata = config.metadata
        opentrons_exe = (
            "opentrons_simulate" if config.run_simulation else "opentrons_execute"
        )
        self.exe = Path(config.opentrons_path) / opentrons_exe

    def imports(self) -> None:
        """Include imports here."""
        raise NotImplementedError

    def generate_template(
        self,
        protocol_path: PathLike,
        funcs: List[Callable[..., Any]] = [],
        template_file: str = "protocol.j2",
    ) -> None:
        write_template(
            Path(protocol_path),
            imports=self.imports,
            config_class=self.protocol_config_class,
            run_func=self.run,
            metadata=self.metadata,
            funcs=funcs,
            template_file=template_file,
        )

    def run_local(self, experiment: Experiment) -> int:
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

    def run_remote(self, experiment: Experiment) -> int:
        assert self.conn is not None

        # /root/test1/experiment-1
        workdir = experiment.cfg.workdir = self.conn.remote_dir / experiment.name
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
        self.conn._scp(experiment.protocol, f"{self.conn.host}:{remote_protocol}")
        self.conn._scp(experiment.yaml, f"{self.conn.host}:{remote_yaml}")

        # Execute remote experiment
        result: Result = self.conn.run(f"{self.exe} {remote_protocol}")
        _write_log(result.stdout, experiment.output_dir / "stdout.log")
        _write_log(result.stderr, experiment.output_dir / "stderr.log")
        returncode: int = result.exited
        if returncode != 0:
            # Return early since something went wrong
            return returncode

        # Transfer experiment results back to local
        self.conn._transfer(experiment, workdir, remote_protocol)

        # Clean up experiment on remote
        self.conn.run(f"rm -r {workdir} {remote_yaml}")

        return returncode
