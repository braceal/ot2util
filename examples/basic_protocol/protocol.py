"""
Example to specifiy protocol parameters in a config as an alternative
to passing them via the command line.

To generate an example yaml config file:
python basic.py

To use with opentrons_simulate or opentrons_execute
opentrons_execute protocol.py -d config.yaml

Modify config.yaml as needed
"""

from typing import List
from opentrons import protocol_api
from ot2util.config import ProtocolConfig, LabwareConfig, InstrumentConfig


class SimpleProtocolConfig(ProtocolConfig):
    # File must be named config
    source_wells: List[str] = ["A1", "A2", "A3"]
    destination_wells: List[str] = ["B1", "B2", "B3"]
    # Volume to aspirate and dispense
    volume: int = 100
    wellplate: LabwareConfig = LabwareConfig(
        name="corning_96_wellplate_360ul_flat", location="2"
    )
    tiprack: LabwareConfig = LabwareConfig(
        name="opentrons_96_tiprack_300ul", location="1"
    )
    pipette: InstrumentConfig = InstrumentConfig(name="p300_single", mount="left")


# metadata
metadata = {
    "protocolName": "My Protocol",
    "author": "Name <email@address.com>",
    "description": "Simple protocol to get started using OT2",
    "apiLevel": "2.12",
}


def run(protocol: protocol_api.ProtocolContext):

    # https://github.com/Opentrons/opentrons/blob/edge/api/src/opentrons/util/entrypoint_util.py#L59
    # protocol.bundled_data["config.yaml"] will contain the raw bytes of the config file
    cfg = SimpleProtocolConfig.from_bytes(protocol.bundled_data["config.yaml"])

    # labware
    plate = protocol.load_labware(cfg.wellplate.name, cfg.wellplate.location)
    tiprack = protocol.load_labware(cfg.tiprack.name, cfg.tiprack.location)

    # pipettes
    pipette = protocol.load_instrument(
        cfg.pipette.name, cfg.pipette.mount, tip_racks=[tiprack]
    )

    # commands
    pipette.pick_up_tip()
    for src_well, dst_well in zip(cfg.source_wells, cfg.destination_wells):
        pipette.aspirate(cfg.volume, plate[src_well])
        pipette.dispense(cfg.volume, plate[dst_well])
    pipette.drop_tip()


if __name__ == "__main__":
    # Write an example yaml file with default settings
    SimpleProtocolConfig().dump_yaml("config.yaml")
