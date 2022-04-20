#ot2util imports 
from ot2util.algorithm import Algorithm 
from ot2util.experiment import Experiment
from ot2util.config import PathLike, parse_args

#from user
from protocol import SimpleProtocolConfig

class GridSearch(Algorithm): 
    def __init__(self, config_path: PathLike) -> None:
        #creates self.config, self.experiment_manager fields
        super().__init__(config_path)

        #number of unique protocols to run 
        self.len = len(str(len(self.config.volume_values)))

        #Make output folder. Not sure if this should be here or elsewhere
        self.config.output_dir.mkdir(exist_ok=True)


    def __len__(self) -> int:
        return  self.len


    def run(self, ) -> None: 

        # Loop over specified volume values and update configuration
        for itr, volume in enumerate(self.config.volume_values):
            #create protocol for individual experiment 
            protocol_cfg = SimpleProtocolConfig.from_yaml("config.yaml")
            
            # Update search parameter
            protocol_cfg.volume = volume

            # Create new experiment
            experiment_name = f"experiment-{itr:0{len(self)}d}"
            if self.config.remote_dir is not None:
                protocol_cfg.workdir = self.config.remote_dir / experiment_name
            experiment = Experiment(
                experiment_name, self.config.output_dir, self.config.protocol, protocol_cfg
            )

            # Run the experiment
            returncode = self.experiment_manager.run(experiment)
            if returncode != 0:
                raise ValueError(
                    f"Experiment {experiment.name} exited with returncode: {returncode}"
                )

def main(config_path):
    gridsearch = GridSearch(config_path)
    print('Running gridsearch')
    gridsearch.run()
    print('Done running gridsearch')
    


if __name__ == "__main__":
    args = parse_args() 
    main(args.config)