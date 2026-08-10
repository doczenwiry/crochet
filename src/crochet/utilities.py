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

import stim


def partition_qubits(circuit: stim.Circuit) -> tuple[Collection[int], Collection[int]]:
    all_qubits = set()
    measurements: Counter[int] = Counter()

    for instruction in circuit.flattened():
        for target in instruction.targets_copy():
            if target.is_qubit_target:
                all_qubits.add(target.value)
            if instruction.name in ["R", "RX", "MR", "MRX"]:
                measurements[target.value] += 1

    data_qubits = set(filter(lambda q: measurements[q] == 1, measurements.keys()))
    ancillas = set(filter(lambda q: measurements[q] > 1, measurements.keys()))

    return data_qubits, ancillas
