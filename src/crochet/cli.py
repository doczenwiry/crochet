#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
import os.path
import sys
from argparse import ArgumentParser

import stim

from crochet.core.plaquette import Plaquette
from crochet.drawing.drawer import Drawer
from crochet.drawing.palette import Palette
from crochet.utilities import get_bounding_box, partition_qubits

parser = ArgumentParser(
    prog="crochet",
    description="A tool to visualize the schedules of a STIM stabilizer circuit for QEC.",
)
parser.add_argument(
    "-f",
    "--fontsize",
    action="store",
    type=int,
    default=16,
    help="set the fontsize to use for the annotations",
)
parser.add_argument(
    "-p",
    "--palette",
    action="store",
    choices=["zx", "schedules"],
    default="zx",
    help="choose whether to color plaquettes by their stabilizer types or take their schedule into account",
)


def int_list(value):
    return [int(x) for x in value.split(",")]


parser.add_argument(
    "-r",
    "--rounds",
    action="store",
    type=int_list,
    help="select which rounds should be visualized.",
)
parser.add_argument(
    "-s",
    "--savefile",
    action="store_true",
    help="toggle whether to save the PNG files that were generated for all the rounds",
)
parser.add_argument("filepath", help="path to a *.stim file")

logging.basicConfig(level=logging.INFO)


def main():
    args = parser.parse_args()

    circuit = stim.Circuit.from_file(args.filepath)
    datas, ancillas, rounds = partition_qubits(circuit)

    print(f"Loaded circuit : {args.filepath}")
    print(f"> Qubits : datas [{len(datas)}], ancillas [{len(ancillas)}]")
    max_number_of_rounds = max(count for _, count in rounds.items())
    print(f"> Number of rounds : {max_number_of_rounds}")

    if len(ancillas) == 0:
        print(
            "> ERROR: Couldn't detect the ancillas by R/M pattern. Either the circuit has no QEC or contains only a single round."
        )
        sys.exit(-1)

    all_rounds = Plaquette.decompose(circuit, datas, ancillas)

    qubit_at_location = {
        (qx, qy): qubit
        for qubit, (qx, qy) in circuit.get_final_qubit_coordinates().items()
    }

    basename, _ = os.path.splitext(args.filepath) if args.savefile else (None, None)

    for r, round in enumerate(all_rounds):
        if args.rounds and r not in args.rounds:
            continue

        Drawer.draw(
            *get_bounding_box(circuit),
            round,
            qubit_at_location,
            style=Palette[args.palette.upper()],
            fontsize=args.fontsize,
            savefile=f"{basename}-r{r}.png" if basename else None,
        )


if __name__ == "__main__":
    main()
