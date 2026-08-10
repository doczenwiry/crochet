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

from argparse import ArgumentParser

import stim

from crochet.utilities import partition_qubits

parser = ArgumentParser(
    prog="crochet",
    description="A tool to visualize the schedules of a STIM stabilizer circuit for QEC.",
)
parser.add_argument("filepath", help="path to a *.stim file")


def main():
    args = parser.parse_args()

    circuit = stim.Circuit.from_file(args.filepath)
    dqubits, aqubits = partition_qubits(circuit)

    print(f"Loaded circuit : {args.filepath}")
    print(f"> Data qubits : {len(dqubits)}")
    print(f"> Ancillaries : {len(aqubits)}")

    # print(f"> Rounds : {find_rounds(circuit)}")
