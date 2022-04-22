import subprocess
from typing import Optional, Union
from pathlib import Path
from fabric import Connection
from invoke.runners import Result
from ot2util.config import ProtocolConfig, PathLike


class Experiment:
    """Encapsulation of a singular experiment. 

    Contains information local to a singular protocol. Will be executed by experiment manager 
    """
    def __init__(
        self,
        name: str,
        output_dir: PathLike,
        protocol: PathLike,
        protocol_cfg: ProtocolConfig,
    ):
        self.name = name
        self.remote_dir = protocol_cfg.workdir
        self.output_dir = Path(output_dir) / name
        self.yaml = self.output_dir / "config.yaml"
        self.protocol = Path(protocol)

        # Create new experiment directory
        self.output_dir.mkdir()
        protocol_cfg.dump_yaml(self.yaml)


class ExperimentManager:
    """Manage a set of experiments to be run in the same session.
    """
    def __init__(
        self,
        run_simulation: bool,
        host: Optional[str] = None,
        port: int = 22,
        key_filename: Optional[str] = None,
        opentrons_path: Path = Path("/bin"),
        tar_transfer: bool = False,
    ):
        """Manage a set of experiments to be run in the same session.

        Parameters
        ----------
        run_simulation : bool
            If True, runs opentrons_simulate instead of opentrons_execute.
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
        self.host = host
        self.key_filename = key_filename
        self.tar_transfer = tar_transfer

        self.conn = None
        if host is not None:
            connect_kwargs = {}
            if key_filename is not None:
                connect_kwargs["key_filename"] = key_filename

            # TODO: Handle authentication in a better way
            self.conn = Connection(host=host, port=port, connect_kwargs=connect_kwargs)
            # TODO: We may be able to add an optional proxy jump to connect
            #       to the robot from a remote location not connected to the
            #       robots local WiFi environment.
            # https://docs.fabfile.org/en/2.6/concepts/networking.html#proxyjump

    def __del__(self) -> None:
        # Close the remote connection
        if self.conn is not None:
            self.conn.close()

    def _write_log(self, contents: Union[str, bytes], path: Path) -> None:
        mode = "wb" if isinstance(contents, bytes) else "w"
        with open(path, mode) as f:
            f.write(contents)

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
        workdir = experiment.remote_dir

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
        # TODO: Test remote_yaml instead of workdir.parent
        self._scp(experiment.yaml, f"{self.host}:{workdir.parent}")

        # Execute remote experiment
        result: Result = self.conn.run(f"{self.exe} {remote_protocol}")
        self._write_log(result.stdout, experiment.output_dir / "stdout.log")
        self._write_log(result.stderr, experiment.output_dir / "stderr.log")
        returncode: int = result.exited
        if returncode != 0:
            # Return early since something went wrong
            return returncode

        # Transfer experiment results back to local
        self._transfer(experiment, workdir, remote_protocol)

        # Clean up experiment on remote
        self.conn.run(f"rm -r {workdir} {remote_yaml}")

        return returncode

    def _run_local(self, experiment: Experiment) -> int:
        # The -d option corresponds to the opentrons custom-data-file argument
        # which passes the config file to the protocol.bundled_data field
        command = f"{self.exe} {experiment.protocol} -d {experiment.yaml}"
        proc = subprocess.run(command, shell=True, capture_output=True)
        self._write_log(proc.stdout, experiment.output_dir / "stdout.log")
        self._write_log(proc.stderr, experiment.output_dir / "stderr.log")
        return proc.returncode

    def run(self, experiment: Experiment) -> int:
        """Execute an experiment object. 

        Will execute an experiment according to the paramters of the experiment. 
        Can determine to run locally or on the OT2. 

        Args:
            experiment (Experiment): Protocol to be run. Contains necesary information to run trial. 

        Returns:
            int: Return code of experiment. 0 is success, anything other than 0 is a failure. 
        """
        if self.conn is None:
            return self._run_local(experiment)
        return self._run_remote(experiment)
