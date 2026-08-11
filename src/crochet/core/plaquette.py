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

import itertools
import logging
from collections.abc import Collection
from enum import Enum

import stim

from crochet.core.common import Moment, Qubit

console = logging.getLogger(__name__)


class StabilizerType(Enum):
    U = 1
    X = 2
    Z = 3


class Plaquette:
    def __init__(self, start: int, location: list[float], size: int = 1):
        self.__start: Moment = start
        self.__location: list[float] = location
        self.__interactions: dict[tuple[float, float], Moment] = {}
        self.__stabilizer_type = StabilizerType.U
        if size == 1:
            self.__corners = [(-0.5, -0.5), (+0.5, -0.5), (-0.5, +0.5), (+0.5, +0.5)]
        elif size == 2:
            self.__corners = []

    @property
    def start(self):
        return self.__start

    @property
    def location(self):
        return self.__location

    @property
    def interactions(self):
        return self.__interactions

    @property
    def stabilizer_type(self) -> StabilizerType:
        return self.__stabilizer_type

    def interact(
        self, moment: int, qubit: int, position: list[float], stype: StabilizerType
    ):
        qpx, qpy = self.__location
        qdx, qdy = position
        location = qdx - qpx, qdy - qpy

        if location in self.__interactions:
            raise ValueError(
                f"Data qubit is accessed twice by Round {qubit} [{self.__location}]."
            )

        if StabilizerType.U != self.__stabilizer_type != stype:
            raise ValueError(
                f"Plaquette is perform different types of controlled stabilizers [{self.__stabilizer_type}/{stype}]"
            )
        else:
            self.__stabilizer_type = stype

        self.__interactions[location] = moment

    @property
    def schedule(self) -> tuple[int, ...]:
        schedule = []
        for c in self.__corners:
            schedule.append(self.__interactions.get(c, -1))
        return tuple(schedule)

    @staticmethod
    def decompose(
        circuit: stim.Circuit, datas: Collection[Qubit], ancillas: Collection[Qubit]
    ) -> list[dict[Qubit, Plaquette]]:
        qubit_coordinates = circuit.get_final_qubit_coordinates()
        rounds_per_ancilla: dict[Qubit, dict[Moment, Plaquette]] = {
            a: {} for a in ancillas
        }

        ticks = 0
        inter_ancilla_interaction_detected = False
        for instruction in circuit.flattened():
            if instruction.name in ["R", "RX", "MR", "MRX"]:
                for tgt in instruction.targets_copy():
                    if tgt.value in ancillas:
                        rounds_per_ancilla[tgt.value][ticks] = Plaquette(
                            ticks, qubit_coordinates[tgt.value]
                        )

            if instruction.name in ["CX", "CZ"]:
                for fst, snd in instruction.target_groups():
                    if fst.value in datas and snd.value in datas:
                        raise ValueError(
                            "Inter-data qubit interaction are not supposed to happen in QEC."
                        )
                    elif fst.value in ancillas and snd.value in ancillas:
                        if not inter_ancilla_interaction_detected:
                            console.warning(
                                "Inter-ancilla qubit interactions are not supported for now."
                            )
                            inter_ancilla_interaction_detected = True
                        continue

                    ctrl, trgt = (
                        (fst.value, snd.value)
                        if fst.value in ancillas
                        else (snd.value, fst.value)
                    )

                    start = max(rounds_per_ancilla[ctrl])
                    current: Plaquette = rounds_per_ancilla[ctrl][start]
                    current.interact(
                        ticks,
                        trgt,
                        qubit_coordinates[trgt],
                        StabilizerType[instruction.name[1]],
                    )

            if instruction.name == "TICK":
                ticks += 1

        number_of_rounds = len(next(iter(rounds_per_ancilla.values())))
        if any(
            len(rounds) != number_of_rounds for rounds in rounds_per_ancilla.values()
        ):
            raise NotImplementedError(
                "Unable to work with a QEC circuit containing different number of rounds per stabilizers."
            )

        plaquettes = []
        for round in range(number_of_rounds):
            layer = {}
            for ancilla, rounds in rounds_per_ancilla.items():
                layer[ancilla] = rounds[
                    next(itertools.islice(rounds.keys(), round, None))
                ]
            plaquettes.append(layer)

        return plaquettes

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "".join(str(m) if m != -1 else "-" for m in self.schedule)
