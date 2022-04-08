### start
import sys
import os
import pandas as pd
from opentrons import protocol_api, simulate, execute
import json
import argparse
### end

"""
Very quickly written example of a template file that creates a correctly formatted 
python protocol for the Opentrons OT-2 based on command line input

Example usage: 
python template.py -s A1 A2 A3 -d B1 B2 B3 -f test1.py
"""

# HELPER METHODS ------------------------------------------------------------------
def write_protocol(source_wells, destination_wells, output_filepath):    
    current_file_path = "/Users/cstone/Desktop/ot2_demo/template.py"

    try: 
        with open(current_file_path, 'r') as open_this: 
            with open(output_filepath, 'w+') as open_that: 
                contents_this = open_this.readlines()
                for i in range(len(contents_this)): 
                    if contents_this[i].startswith("### start"):
                        j = i
                        while not contents_this[j].startswith("### end"): 
                            j+=1
                        open_that.writelines(contents_this[i+1:j])

                    if contents_this[i].startswith("### TL"):
                        open_that.write(f"\nsource_wells = {str(source_wells)}")
                        open_that.write(f"\ndestination_wells = {str(destination_wells)}\n")
                        

        return(f"Protocol created = {output_filepath} ")
    except: 
        return(f"Error: Could not write to protocol file\n{current_file_path}\n{output_filepath}")

# MAIN METHOD --------------------------------------------------------------------

def generate_from_template(source_wells, destination_wells, output_filepath): 

    try: 
        write_protocol(source_wells, destination_wells, output_filepath)
    except OSError as e:  
        raise

    return 


def main(args):
    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--source_wells",
        help="source wells",
        required=True,
        type=str,
        nargs="*",
    )
    parser.add_argument(
        "-d",
        "--destination_wells",
        help="destination wells",
        required=True,
        type=str,
        nargs="*",
    )
    parser.add_argument(
        "-f",
        "--output_filepath",
        help="entire path for output protocol file",
        required=True,
        type=str,
        #nargs="*",
    )

    
    args = vars(parser.parse_args())

    # pass to method
    generate_from_template(
        args["source_wells"],
        args["destination_wells"],
        args["output_filepath"],
    )


if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv)

# ------------------------------------------ contents of protocol --------------------------------------------------
### start 

# metadata
metadata = {
    'protocolName': 'My Protocol',
    'author': 'Name <email@address.com>',
    'description': 'Simple protocol to get started using OT2',
    'apiLevel': '2.12'
}

### end

### TL 

### start 

def run(protocol: protocol_api.ProtocolContext):

    # labware
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')

    # pipettes
    left_pipette = protocol.load_instrument(
         'p300_single', 'left', tip_racks=[tiprack])

    # commands
    left_pipette.pick_up_tip()
    for i in range(len(source_wells)): 
        left_pipette.aspirate(100, plate[source_wells[i]])
        left_pipette.dispense(100, plate[destination_wells[i]])
    left_pipette.drop_tip()


### end 