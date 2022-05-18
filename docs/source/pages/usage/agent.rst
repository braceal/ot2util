How to write an agent
=========================

As of right now, implementing your own agent should be a straightforward process. 

Steps: 
    1. Create a config class like the one shown below::

        class GridSearchConfig(WorkflowConfig):
            # Path to protocol script containing run function
            protocol: Path = ""
            # Base configuration options for the protocol
            base_config: Path = Path("config.yaml")
            # Volume values to grid search
            volume_values: List[int] = [50, 100]

     You should define where the protocols you are running are located, as well as the path to their configurations.
     You should also define any information you will need to run the agent. In this basic example, we have a list
     of volumes we are going to try and search over.

    2. Create your Agent class. Your agent should inherit from :py:class:`~ot2util.agent.Agent`. In the initialization you must call :code:`super().__init__(config)` to initialize the things located in the super class. After that, you must implement the :code:`run` function. This is up to you to design.
        
        * In the run function you must create experiments using your :code:`base_config` and :code:`protocol` files. You do this by specifying :py:class:`Experiment<ot2util.experiment.Experiment>` objects. 
        * You must also set the experiment to run. You do not need to specify which machine (this will be determined automatically), but you do need to tell the utillity to run it.

    An example is shown below: 

    .. literalinclude:: ../../../../examples/gym_test/agent.py
        :linenos:
        :language: python