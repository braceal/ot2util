from pathlib2 import Path
from typing import Any, List, Optional

from yaml import parse

from ot2util.config import BaseSettings, parse_args
from ot2util.experiment import Experiment, ExperimentManager

'''
Things to do: 
    - have to figure out how to set the base algorithm class up with just some of the things 
    found in the config file (extras=True???)
        - can a model have an init? 
        - can a model use methods 
        - should we wrap the pydantic model into a more traditional class? 
    - __str__() and __repr__() methods 
    - figure out how to let run take as many arguments as you need 
    - proper order of making directories and what not during the experiment 
    - what happens if an experiment needs more setup than the base algorithm provides? 


    

Design ideas 
    - Do we do it like pytorch and have every 'model' setup its own forwards function
    (im thinking of calling this the run function)
        - what are the other options? not sure to be honest
    - is it still better to just have the algorithms live in the user space than to itegrate them? 
    - also, I want to change 'remote_dir' to 'workdir' not sure if that causes namespace clashes though 


'''

class Algorithm(BaseSettings): 
    # Remote directory path to stage experiments in
    remote_dir: Optional[Path] = None
    # Remote host i.e. [user@]host[:port]
    host: Optional[str] = None
    # Private key path
    key_filename: Optional[str] = None
    # Path to opentrons_simulate or opentrons_execute directory
    opentrons_path: Path = Path("/usr/bin")
    # Whether or not to tar files before transferring from remote to local
    tar_transfer: bool = False
    # Directory to write experimental results to
    output_dir: Path = ""
    # Path to protocol script containing run function
    protocol: Path = ""
    # Toggle simulation
    run_simulation: bool = True


    def __repr__(self) -> str: 
        return f"{type(self)}()"
    
    def __len__(self) -> int: 
        raise NotImplementedError 

    def run(self, *args: Any, **kwargs: Any) -> None: 
        raise NotImplementedError


def main(args):
    abstract_algorithm = Algorithm.from_yaml(args)
    print(repr(abstract_algorithm))

if __name__ == "__main__":
    args = parse_args() 
    main(args.config)

        