How to write YAML
================= 

Writing an Algorithm YAML
################################

Running a Simulation Algorithm
******************************

Fields 
^^^^^^^
    - :code:`remote_dir: Optional[Path]` a pathlike object pointing to place to stage experiments on remote OT2 pointing
    - :code:`host: Optional[str]` remote host i.e. :code:`[user@]host`
    - :code:`port: int` port to connect via ssh. Defaults to 22 
    - :code:`key_filename: Optional[Path]` path to private key for OT2 
    - :code:`opentrons_path: Optional[Path]` path to opentrons_simulate/opentrons_execute programs (point to bin folder they exist in)
    - :code:`tar_transfer: bool` whether to tar files before transferring from remote to local. Slow operation, avoid if possible 
    - :code:`output_dir: Path` directory to write experimental results to
    - :code:`protocol: Path` path to protocol script to run protocol 
    - :code:`run_simulation: bool` whether or not to run a simulation of protocol or execute on OT2

These values are the values that should be present in any algorithm. You can run an simulation remotely on 
the OT2 pi, and if you do these fields will be required, but if you just want to run a simulation on your local 
computer, do not include :code:`remote_dir, host, port, key_filename, tar_transfer`. 
fields in your YAML. Below is an example of a grid search algorithm yaml file. 

.. literalinclude:: ../../../../examples/basic_protocol/grid_search_local.yaml
    :linenos:
    :language: yaml

Other values, such as :code:`volume_values` above, will be available for you to use in your algorithm, but are not 
required by the ot2util package. You can include any valid yaml here and it will be accessible in your aglorithm. 

Running an Algorithm on OT2
*****************************

Fields 
^^^^^^^
    - :code:`remote_dir: Optional[Path]` a pathlike object pointing to place to stage experiments on remote OT2 pointing
    - :code:`host: Optional[str]` remote host i.e. :code:`[user@]host`
    - :code:`port: int` port to connect via ssh. Defaults to 22 
    - :code:`key_filename: Optional[Path]` path to private key for OT2 
    - :code:`opentrons_path: Optional[Path]` path to opentrons_simulate/opentrons_execute programs (point to bin folder they exist in)
    - :code:`tar_transfer: bool` whether to tar files before transferring from remote to local. Slow operation, avoid if possible 
    - :code:`output_dir: Path` directory to write experimental results to
    - :code:`protocol: Path` path to protocol script to run protocol 

These fields are available for running an algorithm on the OT2. :code:`tar_transfer` is not required, but will default to false. 
An example of the grid_search algorithm yaml run on the OT2 is shown below. 

.. literalinclude:: ../../../../examples/basic_protocol/grid_search_remote.yaml
    :linenos:
    :language: yaml



Writing a Protocol YAML
########################

Protocol YAMLs are what acompany individual protocols (algorithms run many protocols, protocols are the instructions of the experiment.)
Protocols include information regarding the setup of the OT2, and which items to move where and so on. 

Fields 
^^^^^^^
    - :code:`source_wells: list[str]` list of strings refering to location in the wellplate of source materials
    - :code:`destination_wells: list[str]` list of strings referring to location in the wellplate of destination location 
    - :code:`volume: int` integer reffering to volume of liquid to aspirate/dispense 
    - :code:`wellplate: dict{name:str, location:str}` wellplate object, need to know what it is and where it is 
    - :code:`pipette: dict{name:str, mount:str}` pipette on the machine, need to know what it is and where it is

Below is an example protocol yaml file: 

.. literalinclude:: ../../../../examples/basic_protocol/config.yaml
    :linenos:
    :language: yaml
