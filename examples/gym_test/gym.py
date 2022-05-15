from typing import List, Set, Dict, Union
from opentrons.protocol_api import ProtocolContext
from ot2util.config import (
    ProtocolConfig,
    LabwareConfig,
    InstrumentConfig,
    MetaDataConfig,
)
from ot2util.gym import Robot


class ColorMixingProtocolConfig(ProtocolConfig):
    # File must be named config
    source_wells: List[str] = ["A1", "A2", "A3"]
    source_volumes: List[int] = [10, 5, 10]
    # Volume to aspirate and dispense
    tips: List[str] = ["A1", "A2", "A3"]
    """Each experiment needs to specify all of the tips it
    will use to mix the three colors."""
    target_well: str = "B1"
    wellplate: LabwareConfig
    tiprack: LabwareConfig
    pipette: InstrumentConfig
    sourceplate: LabwareConfig


def next_location(cur_location: str) -> str:
    letter = cur_location[0]
    number = cur_location[1:]
    if number == "12":
        number = "1"
        letter = chr(ord(letter) + 1)
    else:
        number = str(int(number) + 1)
    if letter == "I" and number == "12":
        return ""
    return letter + number


class WellPlate:
    def __init__(self, name: str, location: str, reserved: Set[str] = set()):
        self.config = LabwareConfig(name=name, location=location)
        self.reserved = reserved

    def get_open_well(self) -> str:
        # TODO: If empty, raise error.
        #       Or instead of raising error, return None.
        # while True:
        #     well = self.get_well()
        #     if well not in self.reserved:
        #         return well
        return ""


class Tiprack:
    def __init__(self, name: str, location: str):
        self.config = LabwareConfig(name=name, location=location)

    def get_tip(self) -> str:
        # TODO: If empty, raise error.
        #       Or instead of raising error, return None.
        return ""

    def get_tips(self, n: int) -> List[str]:
        """Get a list of unused tip positions.

        Parameters
        ----------
        n : int
            Number of tips to return.

        Returns
        -------
        List[str]
            The next :code:`n` available tip locations.
        """
        return [self.get_tip() for _ in range(n)]


class ColorMixingRobot(Robot):
    config_class = ColorMixingProtocolConfig

    def __init__(self, metadata: Union[MetaDataConfig, Dict[str, str]]):
        super().__init__(metadata)
        # Reserve 3 wells for the primary colors to mix
        self.wellplate = WellPlate(
            name="corning_96_wellplate_360ul_flat",
            location="2",
            reserved=set(["A5", "A6"]),
        )
        self.tiprack = Tiprack(name="opentrons_96_tiprack_300ul", location="1")
        self.pipette = InstrumentConfig(name="p300_single", mount="left")
        self.sourceplate = LabwareConfig(
            name="corning_6_wellplate_16.8ml_flat", location="3"
        )

    def submit(self, source_wells: List[str], source_volumes: List[str]) -> None:

        target_well: str = self.wellplate.get_open_well()
        tips: List[str] = self.tiprack.get_tips(n=3)

        config = ColorMixingProtocolConfig(
            source_wells=source_wells,
            source_volumes=source_volumes,
            tips=tips,
            target_well=target_well,
            wellplate=self.wellplate.config,
            tiprack=self.tiprack.config,
            pipette=self.pipette,
            sourceplate=self.sourceplate,
        )
        print(config)
        return config

        # TODO: Threading logic for submitting to real opentrons
        # TODO: Generate template protocol and submit config to job
        workdir = ""
        self.generate_template(workdir + "/protocol.py")

    def imports(self) -> None:
        """This protocol implements the color mixing gym."""
        from typing import List  # noqa
        from opentrons.protocol_api import ProtocolContext  # noqa
        from ot2util.config import (  # noqa
            ProtocolConfig,
            LabwareConfig,
            InstrumentConfig,
        )

    # TODO: As an alternative to implementing the run function
    #       you can use the protopiler interface to implement the
    #       run function.
    def run(protocol: ProtocolContext) -> None:

        # Load the protocol configuration
        cfg = ColorMixingProtocolConfig.get_config(protocol)

        # labware
        wellplate = protocol.load_labware(cfg.wellplate.name, cfg.wellplate.location)
        tiprack = protocol.load_labware(cfg.tiprack.name, cfg.tiprack.location)
        sourceplate = protocol.load_labware(
            cfg.sourceplate.name, cfg.sourceplate.location
        )

        # pipettes
        pipette = protocol.load_instrument(
            cfg.pipette.name, cfg.pipette.mount, tip_racks=[tiprack]
        )

        # commands
        for src_well, src_volume, tip in zip(
            cfg.source_wells, cfg.source_volumes, cfg.tips
        ):
            pipette.pick_up_tip(location=tiprack.wells_by_name()[tip])
            pipette.aspirate(src_volume, sourceplate[src_well])
            pipette.dispense(src_volume, wellplate[cfg.target_well])
            pipette.drop_tip()


# TODO: Probably need an interface here.
class Gym:
    def __init__(self):
        pass


class ColorMixingGym(Gym):
    def __init__(self, metadata: Union[MetaDataConfig, Dict[str, str]]):
        # Define envirnomental parameters
        self.camera = None
        # TODO: Have a list of ColorMixingRobots
        self.robot = ColorMixingRobot(metadata)
        # self.protopiler = Protopiler()

    def action(self, c1: str, c2: str, c3: str, v1: int, v2: int, v3: int):
        # TODO: Color is probably a data type with name and location (Namedtuple).
        #       Suppose for now they are location names e.g. "A1"

        source_wells = [c1, c2, c3]
        source_volumes = [v1, v2, v3]

        self.robot.submit(source_wells, source_volumes)

        # TODO: Maybe it's a good idea to submit action to a thread pool
        #       so we can block the thread until the protocol is finished
        #       and then have it run the camera command all in the same thread.
        #       if we go this route, some of the functions like get_open_well()
        #       and get_tips() need to be thread safe (though perhaps if each robot
        #       has it's own labware then this is not necessary since a robot can
        #       only accept one job at a time).

    def state(self):
        pass


metadata = {
    "protocolName": "My Protocol",
    "author": "Name <email@address.com>",
    "description": "Simple protocol to get started using OT2",
    "apiLevel": "2.12",
}

if __name__ == "__main__":
    robot = ColorMixingRobot(metadata=metadata)
    # TODO: Next location is not needed, just present for testing purposes
    # robot.generate_template("test_protocol.py", funcs=[next_location])

    cfg = robot.submit(["A1", "A2", "A3"], [10, 10, 10])
    cfg.write_yaml("color_test.yaml")
