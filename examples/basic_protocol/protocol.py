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
from pathlib import Path
from opentrons import protocol_api
from ot2util.config import (
    ProtocolConfig,
    LabwareConfig,
    InstrumentConfig,
    ExperimentResult,
)


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


class SimpleProtocolConfig(ProtocolConfig):
    # File must be named config
    source_wells: List[str] = ["A1", "A2", "A3"]
    source_volumes: List[int] = [10, 5, 10]
    # Volume to aspirate and dispense
    target_tip: str = "A1"
    target_well: str = "B1"
    wellplate: LabwareConfig = LabwareConfig(
        name="corning_96_wellplate_360ul_flat", location="2"
    )
    tiprack: LabwareConfig = LabwareConfig(
        name="opentrons_96_tiprack_300ul", location="1"
    )
    pipette: InstrumentConfig = InstrumentConfig(name="p300_single", mount="left")
    sourceplate: LabwareConfig = LabwareConfig(
        name="corning_6_wellplate_16.8ml_flat", location="3"
    )


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
    # TODO: There is a bug in the opentrons code which does not pass this parameter
    #       correctly during opentrons_execute commands.
    if "config.yaml" in protocol.bundled_data:
        cfg = SimpleProtocolConfig.from_bytes(protocol.bundled_data["config.yaml"])
    else:
        # As a quick fix, we hard code a path to write config files to.
        remote_dir = Path("/root/test1")
        cfg = SimpleProtocolConfig.from_yaml(remote_dir / "config.yaml")

    target_tip = cfg.target_tip
    target_well = cfg.target_well
    # next_empty_well = protocol_cfg.next_empty_well
    source_wells = cfg.source_wells
    source_volumes = cfg.source_volumes

    # labware
    plate = protocol.load_labware(cfg.wellplate.name, cfg.wellplate.location)
    tiprack = protocol.load_labware(cfg.tiprack.name, cfg.tiprack.location)
    sourceplate = protocol.load_labware(cfg.sourceplate.name, cfg.sourceplate.location)
    # pipettes
    pipette = protocol.load_instrument(
        cfg.pipette.name, cfg.pipette.mount, tip_racks=[tiprack]
    )

    # commands
    for i, src_well in enumerate(source_wells):
        pipette.pick_up_tip(location=tiprack.wells_by_name()[target_tip])
        pipette.aspirate(source_volumes[i], sourceplate[src_well])
        pipette.dispense(source_volumes[i], plate[target_well])
        pipette.drop_tip()
        target_tip = next_location(target_tip)
        if target_tip == "":
            raise Exception("No more tips")

    result = {
        "next_target_tip": target_tip,
        "cur_target_well": target_well,
        "next_target_well": next_location(target_well),
    }
    experiment_result = ExperimentResult(**result)
    experiment_result.dump_yaml(cfg.workdir / "experiment_result.yaml")
    # (cfg.workdir / "experiment-result").touch()


if __name__ == "__main__":
    # Write an example yaml file with default settings
    SimpleProtocolConfig().write_yaml("config.yaml")
