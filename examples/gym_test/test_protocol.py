"""This protocol implements the color mixing gym."""
from typing import List  # noqa
from opentrons.protocol_api import ProtocolContext  # noqa
from ot2util.config import (  # noqa
    ProtocolConfig,
    LabwareConfig,
    InstrumentConfig,
)


metadata = {
    "protocolName": "My Protocol",
    "author": "Name <email@address.com>",
    "description": "Simple protocol to get started using OT2",
    "apiLevel": "2.12",
}


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


def run(protocol: ProtocolContext) -> None:

    # Load the protocol configuration
    cfg = ColorMixingProtocolConfig.get_config(protocol)

    # labware
    wellplate = protocol.load_labware(cfg.wellplate.name, cfg.wellplate.location)
    tiprack = protocol.load_labware(cfg.tiprack.name, cfg.tiprack.location)
    sourceplate = protocol.load_labware(cfg.sourceplate.name, cfg.sourceplate.location)
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
