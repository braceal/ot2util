import subprocess
from typing import Optional, Union
from pathlib import Path
from fabric import Connection
from invoke.runners import Result
from ot2util.config import ProtocolConfig, PathLike


class Experiment:
    def __init__(
        self,
        name: str,
        output_dir: PathLike,
        protocol_script: PathLike,
        protocol_cfg: ProtocolConfig,
    ):
        self.name = name
        self.remote_dir = protocol_cfg.workdir
        self.output_dir = Path(output_dir) / name
        self.yaml = self.output_dir / "config.yaml"
        self.protocol_script = Path(protocol_script)

        # Create new experiment directory
        self.output_dir.mkdir()
        protocol_cfg.dump_yaml(self.yaml)


class ExperimentManager:
    def __init__(
        self,
        run_simulation: bool,
        host: Optional[str] = None,
        key_filename: Optional[str] = None,
        opentrons_path: Path = Path("/usr/bin"),
    ):
        """Manage a set of experiments to be run in the same session.

        Parameters
        ----------
        run_simulation : bool
            If True, runs opentrons_simulate instead of opentrons_execute.
        host : Optional[str], optional
            If specified will connect to the opentrons raspberry pi over
            ssh and allow jobs to be run remotely. To specify :obj:`host`
            use the following format [user@]host[:port]. For example,
            "deploy@web1:2202".
        key_filename : Optional[str], optional
            If :obj:`host` is specified, a path to your private key file
            must be supplied to the Fabric Connection. For example,
            "/home/myuser/.ssh/private.key".
        """
        self.exe = "opentrons_simulate" if run_simulation else "opentrons_execute"
        self.exe = Path(opentrons_path) / self.exe


        self.conn = None
        if host is not None:
            #if key_filename is None:
            #    raise ValueError("Path to private key file required. See key_filename.")

            self.conn = Connection(
                host=host,
                port=22,
                connect_kwargs={"password": "locobot"},
            )
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

    def _command_template(self, protocol_script: Path, yaml_path: Path) -> str:
        return f"{self.exe} {protocol_script} -d {yaml_path}"

    def _run_remote(self, experiment: Experiment) -> int:
        assert self.conn is not None

        workdir = experiment.remote_dir
        # Transfer protocol file and configuration over to remote
        self.conn.run(f"mkdir -p {workdir}") # TODO: Add clean up. Create experiment dir in constructor and remove in destructor.
        self.conn.put(experiment.protocol_script, str(workdir))
        self.conn.put(experiment.yaml, str(workdir))

        # Adjust paths to remote workdir
        remote_protocol = workdir / experiment.protocol_script.name
        remote_yaml = workdir / experiment.yaml.name
        command = self._command_template(remote_protocol, remote_yaml)

        # Execute remote experiment
        result: Result = self.conn.run(command)
        self._write_log(result.stdout, experiment.output_dir / "stdout.log")
        self._write_log(result.stderr, experiment.output_dir / "stderr.log")
        returncode: int = result.exited
        if returncode != 0:
            # Return early since something went wrong
            return returncode

        # Transfer experiment results back to local
        remote_tar = workdir.parent / f"{experiment.name}.tar.gz"
        local_tar = str(experiment.output_dir / remote_tar.name)
        excludes = f'--exclude="{remote_protocol.name}" --exclude="{remote_yaml.name}"'
        self.conn.run(f"cd {workdir.parent} && tar {excludes} -czvf {remote_tar} {workdir.name}")
        self.conn.get(str(remote_tar), local=local_tar)
        # Clean up the experiment on remote # TODO: test this
        self.conn.run(f"rm -r {workdir} {remote_tar}")
        # Extract payload into experiment output directory
        #local_tar = experiment.output_dir / remote_tar.name # remove
        subprocess.run(f"tar -xf {local_tar} -C {experiment.output_dir}", shell=True)
        subprocess.run(f"mv {experiment.output_dir / experiment.name}/* {experiment.output_dir}", shell=True)
        subprocess.run(f"rm -r {experiment.output_dir / experiment.name} {local_tar}", shell=True)

        return returncode

    def _run_local(self, experiment: Experiment) -> int:
        # The -d option corresponds to the opentrons custom-data-file argument
        # which passes the config file to the protocol.bundled_data field
        command = self._command_template(experiment.protocol_script, experiment.yaml)
        proc = subprocess.run(command, shell=True, capture_output=True)
        self._write_log(proc.stdout, experiment.output_dir / "stdout.log")
        self._write_log(proc.stderr, experiment.output_dir / "stderr.log")
        return proc.returncode

    def run(self, experiment: Experiment) -> int:
        if self.conn is None:
            return self._run_local(experiment)
        return self._run_remote(experiment)
