from typing import List, Set
from ot2util.config import ProtocolConfig, LabwareConfig, InstrumentConfig


class ColorMixingProtocolConfig(ProtocolConfig):
    # File must be named config
    source_wells: List[str] = ["A1", "A2", "A3"]
    source_volumes: List[int] = [10, 5, 10]
    # Volume to aspirate and dispense
    target_tips: str = ["A1", "A2", "A3"]
    """Each experiment needs to specify all of the tips it
    will use to mix the three colors."""
    target_well: str = "B1"
    wellplate: LabwareConfig
    tiprack: LabwareConfig
    pipette: InstrumentConfig
    sourceplate: LabwareConfig


class WellPlate:
    def __init__(self, reserved: Set[str], location: str, name: str):
        self.reserved = reserved
        self.location = location
        self.name = name


class Tiprack:
    def __init__(self, location: str, name: str):
        self.location = location
        self.name = name


class Robot:
    def __init__(self):
        self.labware = None
        self.instruments = None
        # Reserve 3 wells for the primary colors to mix
        # TODO: Actually, that is what the sourceplate is for,
        #       but it might still be useful to have reserved option
        self.wellplate = WellPlate(
            reserved={"A1", "B1", "C1"},
            location="2",
            name="corning_96_wellplate_360ul_flat",
        )
        self.tiprack = Tiprack(name="opentrons_96_tiprack_300ul", location="1")
        self.pipette: InstrumentConfig = InstrumentConfig(
            name="p300_single", mount="left"
        )
        self.sourceplate: LabwareConfig = LabwareConfig(
            name="corning_6_wellplate_16.8ml_flat", location="3"
        )


class ColorMixingGym:
    def __init__(self):
        # Define envirnomental parameters
        self.camera = None
        self.robot = Robot()
        # self.protopiler = Protopiler()

    def action(self, c1: str, c2: str, c3: str, v1: int, v2: int, v3: int):
        # TODO: Color is probably a data type with name and location (Namedtuple).
        #       Suppose for now they are location names e.g. "A1"
        target_well: str = self.robot.wellplate.get_open_well()
        tip1: str = self.tiprack.get_tip()
        tip2: str = self.tiprack.get_tip()
        tip3: str = self.tiprack.get_tip()

        # TODO: implement get_tip_row for high throughput
        # TODO: Combine LabwareConfig/Wellplate with pydantic dataclasses (needs refactor)
        config = ColorMixingProtocolConfig(
            source_wells=[c1, c2, c3],
            source_volumes=[v1, v2, v3],
            target_tips=[tip1, tip2, tip3],
            target_well=target_well,
            wellplate=LabwareConfig(
                self.robot.wellplate.name, self.robot.wellplate.location
            ),
            tiprack=LabwareConfig(self.robot.tiprack.name, self.robot.tiprack.location),
            pipette=self.robot.pipette,
            sourceplate=self.robot.sourceplate,
        )
        self.run(config)

    def run(config: ColorMixingProtocolConfig):
        # TODO: Can expose interface to write your run function here which
        #       will generate a protocol script from a template.
        # TODO: Could pass metadata through the Gym constructor
        # TODO: As an alternatively to implementing the run function
        #       you can use the protopiler interface to implement the
        #       run function.
        pass
        # This is what we currently do
        # 1. write config yaml
        # 2. send config and protocol to OT2 (assumes protocol is written)
        # Instead see above

        # self.protopiler.compile(cfg)

    def state(self):
        pass
