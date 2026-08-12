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

from collections import Counter
from collections.abc import Collection
from math import ceil

import stim

from crochet.core.common import Qubit


def get_bounding_box(circuit: stim.Circuit) -> tuple[int, int]:
    coordinates = circuit.get_final_qubit_coordinates().values()
    min_x, max_x = (
        min(coordinates, key=lambda pos: pos[0])[0],
        max(coordinates, key=lambda pos: pos[0])[0],
    )
    min_y, max_y = (
        min(coordinates, key=lambda pos: pos[1])[1],
        max(coordinates, key=lambda pos: pos[1])[1],
    )
    return ceil(max_x - min_x), ceil(max_y - min_y)


def partition_qubits(
    circuit: stim.Circuit,
) -> tuple[Collection[Qubit], Collection[Qubit]]:
    all_qubits = set()
    resets: Counter[int] = Counter()

    for instruction in circuit.flattened():
        for target in instruction.targets_copy():
            if target.is_qubit_target:
                all_qubits.add(target.value)
            if instruction.name in ["R", "RX", "MR", "MRX"]:
                resets[target.value] += 1

    datas = set(filter(lambda q: resets[q] == 1, resets.keys()))
    ancillas = set(filter(lambda q: resets[q] > 1, resets.keys()))

    return datas, ancillas
