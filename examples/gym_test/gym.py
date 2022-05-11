import inspect
from typing import List, Set, Dict, Callable, Any
from opentrons.protocol_api import ProtocolContext
from ot2util.config import ProtocolConfig, LabwareConfig, InstrumentConfig


class ColorMixingProtocolConfig(ProtocolConfig):
    # File must be named config
    source_wells: List[str] = ["A1", "A2", "A3"]
    source_volumes: List[int] = [10, 5, 10]
    # Volume to aspirate and dispense
    tips: str = ["A1", "A2", "A3"]
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
    def __init__(self, reserved: Set[str], location: str, name: str):
        self.reserved = reserved
        self.location = location
        self.name = name

    def get_open_well(self) -> str:
        # TODO: If empty, raise error.
        return ""


class Tiprack:
    def __init__(self, location: str, name: str):
        self.location = location
        self.name = name

    def get_tip(self) -> str:
        # TODO: If empty, raise error.
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


metadata = {
    "protocolName": "My Protocol",
    "author": "Name <email@address.com>",
    "description": "Simple protocol to get started using OT2",
    "apiLevel": "2.12",
}


class ColorMixingGym:
    def __init__(self, metadata: Dict[str, str]):
        # Define envirnomental parameters
        self.camera = None
        self.robot = Robot()
        # TODO: Pass metadata to the templating function
        self.metadata = metadata
        # self.protopiler = Protopiler()

    # TODO: These functions should be part of templating code
    def _getsource(self, func: Callable[..., Any]) -> str:
        code = inspect.getsource(func)
        lines = code.split("\n")
        indent = len(lines[0]) - len(lines[0].lstrip())
        lines = [line[indent:] for line in lines]
        code = "\n".join(lines)
        return code

    def add_functions(self, funcs: List[Callable[..., Any]]) -> List[str]:
        # TODO: Should copy into template in the order they are passed
        source_codes = [self._getsource(func) for func in funcs]
        return source_codes

    def action(self, c1: str, c2: str, c3: str, v1: int, v2: int, v3: int):
        # TODO: Color is probably a data type with name and location (Namedtuple).
        #       Suppose for now they are location names e.g. "A1"
        target_well: str = self.robot.wellplate.get_open_well()
        target_tips: List[str] = self.robot.get_tips(n=3)

        # TODO: implement get_tip_row for high throughput
        # TODO: Combine LabwareConfig/Wellplate with pydantic dataclasses (needs refactor)
        config = ColorMixingProtocolConfig(
            source_wells=[c1, c2, c3],
            source_volumes=[v1, v2, v3],
            target_tips=target_tips,
            target_well=target_well,
            wellplate=LabwareConfig(
                self.robot.wellplate.name, self.robot.wellplate.location
            ),
            tiprack=LabwareConfig(self.robot.tiprack.name, self.robot.tiprack.location),
            pipette=self.robot.pipette,
            sourceplate=self.robot.sourceplate,
        )
        self.run(config)

    def run_(config: ColorMixingProtocolConfig):
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

    # TODO: Could consider using the template to auto input the parameters so
    #       we don't need to send or parse the configuration yaml
    def run(protocol: ProtocolContext):

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

    def state(self):
        pass


if __name__ == "__main__":
    gym = ColorMixingGym()
    source_codes = gym.add_functions([next_location, gym.run])
    for code in source_codes:
        print(code)
