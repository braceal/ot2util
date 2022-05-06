from pathlib import Path
from typing import Any, Optional


from ot2util.config import BaseSettings, parse_args, PathLike
from ot2util.experiment import ExperimentManager

'''
Things to do: 
    - proper order of making directories and what not during the experiment 
        - remote_dir is confusing me, want to change to workdir, set working files regardless 
            of working remotely or locally here. Or add a check to make sure we aren't using 
            remote_dir when running locally (host == None?)
    - what happens if an experiment needs more setup than the base algorithm provides? 
    - abstract experiments out further? a little bit of confusion is creaetd 
        when creating the experiment in the run method 
    - figure out how to handle individual protocol failure.
        - store dependecies? If it is critical, cancel experiment, if not, continue without it? 
    - what do we think about users defining their protocol config yaml. should 
        we have an extensible way to do this? is there some universal parser that can take directions 
        and produce an arbitrary protocol file? right now we are limited to running 
        a specific number of aspirations/dispenses/well_moves/ so on. Probably not 
        supposed to be in the algorithm class, but good to think about none the less. 

    
Design ideas 
    - Do we do it like pytorch and have every 'model' setup its own forwards function
    (im thinking of calling this the run function)
        - what are the other options? not sure to be honest
    - is it still better to just have the algorithms live in the user space than to itegrate them? 
'''

class Algorithm_Config(BaseSettings):
    """Configuration for Algorithm super class. Contains data that should be present in any search algorithm 
    for OT2. Any additional information will be ignored. 

    TODO: 
        - Think about storing information better. Currently just allowing 
        extra fields to be added from the users config. Not the worst solution 
        but potentially troublesome. 
    """

    class Config:  
        extra = "allow"

    # Remote directory path to stage experiments in
    remote_dir: Optional[Path] = None
    # Remote host i.e. [user@]host[:port]
    host: Optional[str] = None
    # Private key path
    key_filename: Optional[PathLike] = None
    # Path to opentrons_simulate or opentrons_execute directory
    opentrons_path: PathLike = Path("/usr/bin")
    # Whether or not to tar files before transferring from remote to local
    tar_transfer: bool = False
    # Directory to write experimental results to
    output_dir: Path = Path("")
    # Path to protocol script containing run function
    protocol: PathLike = ""
    # Toggle simulation
    run_simulation: bool = True


class Algorithm:
    """Super class for user implemented search algorithms. Users should implement `run()`
    """
    def __init__(self, config_path: PathLike) -> None:
        """Initialize the algorithm superclass. Will only create the config model. 

        Args:
            config_path (PathLike): Path to YAML config file. 
        """
        #create config object, continas info about experiments to run
        self.config = Algorithm_Config.from_yaml(config_path)
        #create experiment manager 
        self.experiment_manager = ExperimentManager(
                            self.config.run_simulation,
                            self.config.host,
                            self.config.key_filename,
                            self.config.opentrons_path,
                            self.config.tar_transfer 
        )
    
    def __repr__(self) -> str: 
        return f"{type(self)}"

    def __str__(self) -> str: 
        
        return f"{type(self)}({self.config.json()})"

    #User should implement this
    def run(self, *args: Any, **kwargs: Any) -> None: 
        raise NotImplementedError


def main(args):
    abstract_algorithm = Algorithm(args)
    print(abstract_algorithm)

if __name__ == "__main__":
    args = parse_args() 
    main(args.config)

        