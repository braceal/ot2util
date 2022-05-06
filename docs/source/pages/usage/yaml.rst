How to write YAML
================= 

Writing an Algorithm YAML
################################

Running a Simulation Algorithm
******************************

Things needed: 
    * An output directory (part of :py:class:`Experiment<ot2util.config.ExperimentConfig>`)
    * A protocol file and accompanying configuration to run (part of :py:class:`Experiment<ot2util.config.ExperimentConfig>`)
    * Flag to run the sumulation :code:`run_simulation: True` (part of :py:class:`Experiment<ot2util.config.ExperimentConfig>`)

These values should be present in any simulation you run. Adding information from other classes could result in exceptions. 
An example of a local grid search simulation is shown below. 

.. literalinclude:: ../../../../examples/basic_protocol/grid_search_local.yaml
    :linenos:
    :language: yaml

Other values, such as :code:`volume_values` above, will be available for you to use in your algorithm, but are not 
required by the ot2util package. You can include any valid yaml here and it will be accessible in your aglorithm. 

Running an Algorithm on OT2
*****************************

Things Needed: 
    * List of robots (see :py:class:`~ot2util.config.OpentronsConfig`)
    * An output directory (part of :py:class:`Experiment<ot2util.config.ExperimentConfig>`)
    * A protocol file and accompanying configuration to run (part of :py:class:`Experiment<ot2util.config.ExperimentConfig>`)
    * Flag to run the sumulation :code:`run_simulation: False` (part of :py:class:`Experiment<ot2util.config.ExperimentConfig>`)

Other values, such as :code:`volume_values` above, will be available for you to use in your algorithm, but are not 
required by the ot2util package. You can include any valid yaml here and it will be accessible in your aglorithm. 

.. literalinclude:: ../../../../examples/basic_protocol/grid_search_remote.yaml
    :linenos:
    :language: yaml



Writing a Protocol YAML
########################

Protocol YAMLs are what acompany individual protocols (algorithms run many protocols, protocols are the instructions of the experiment.)
Protocols include information regarding the setup of the OT2, and which items to move where and so on. 

Things that are needed:
    * One or more wellplate (:py:class:`Labware<ot2util.config.LabwareConfig>`) objects
    * One or more tiprack (:py:class:`Labware<ot2util.config.LabwareConfig>`) objects
    * One or two pipette (:py:class:`Instrument<ot2util.config.InstrumentConfig>`) objects

Optionally, the user can define other things to go into this file that would specify particulars of the protocol. Users
would have to make a config object to handle this, but as long as your config has the required objects specified above, it will work. 


Below is an example protocol yaml file: 

.. literalinclude:: ../../../../examples/basic_protocol/config.yaml
    :linenos:
    :language: yaml
