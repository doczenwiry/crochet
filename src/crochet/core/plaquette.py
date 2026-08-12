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

import stim

from crochet.core.common import Moment, PauliBasis, Qubit
from crochet.utils.geometry import Geometry

console = logging.getLogger(__name__)


class Plaquette:
    def __init__(self, start: int, basis: PauliBasis, location: list[float]):
        self.__start: Moment = start
        self.__location: list[float] = location
        self.__interactions: dict[tuple[float, float], Moment] = {}
        self.__preparation = basis
        self.__stabilizer_type = PauliBasis.U

    @property
    def start(self):
        return self.__start

    @property
    def location(self):
        return self.__location

    @property
    def basis(self):
        return self.__preparation

    @property
    def corners(self):
        return self.__interactions.keys()

    @property
    def interactions(self):
        return self.__interactions

    @property
    def stabilizer_type(self) -> PauliBasis:
        return self.__stabilizer_type

    def interact(
        self, moment: int, qubit: int, position: list[float], stabilizer: PauliBasis
    ):
        qpx, qpy = self.__location
        qdx, qdy = position
        location = qdx - qpx, qdy - qpy

        if location in self.__interactions:
            raise ValueError(
                f"Data qubit is accessed twice by Round {qubit} [{self.__location}]."
            )

        if PauliBasis.U != self.__stabilizer_type != stabilizer:
            raise ValueError(
                f"Plaquette is perform different types of controlled stabilizers [{self.__stabilizer_type}/{stabilizer}]"
            )
        else:
            self.__stabilizer_type = stabilizer

        self.__interactions[location] = moment

    @property
    def schedule(self) -> tuple[int, ...]:
        schedule = []
        points = sorted((Geometry.theta(*p), p) for p in self.__interactions)
        for _, p in points:
            schedule.append(self.__interactions.get(p, -1))
        return tuple(schedule)

    @staticmethod
    def decompose(
        circuit: stim.Circuit, datas: Collection[Qubit], ancillas: Collection[Qubit]
    ) -> list[dict[Qubit, Plaquette]]:
        qubit_coordinates = circuit.get_final_qubit_coordinates()
        rounds_per_ancilla: dict[Qubit, dict[Moment, Plaquette]] = {
            a: {} for a in ancillas
        }

        current: Plaquette

        ticks = 0
        inter_ancilla_interaction_detected = False
        for instruction in circuit.flattened():
            if instruction.name.startswith("R") or instruction.name.startswith("MR"):
                basis = (
                    PauliBasis.Z
                    if instruction.name in ["R", "MR"]
                    else PauliBasis[instruction.name[-1]]
                )
                for tgt in instruction.targets_copy():
                    if tgt.value in ancillas:
                        rounds_per_ancilla[tgt.value][ticks] = Plaquette(
                            start=ticks,
                            basis=basis,
                            location=qubit_coordinates[tgt.value],
                        )

            if instruction.name == "H":
                for tgt in instruction.targets_copy():
                    if tgt.value in ancillas:
                        ancilla = tgt.value
                        start = max(rounds_per_ancilla[ancilla])
                        current = rounds_per_ancilla[ancilla][start]
                        if ticks == start + 1:
                            current.__preparation = (
                                PauliBasis.X
                                if current.basis == PauliBasis.Z
                                else PauliBasis.Z
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

                    ctrl, trgt = fst.value, snd.value
                    ancilla, data = (ctrl, trgt) if ctrl in ancillas else (trgt, ctrl)

                    start = max(rounds_per_ancilla[ancilla])
                    current = rounds_per_ancilla[ancilla][start]

                    if (
                        current.basis == PauliBasis.X
                        and ctrl == ancilla
                        and trgt == data
                    ):
                        stype = PauliBasis[instruction.name[1]]
                    elif (
                        current.basis == PauliBasis.Z
                        and ctrl == data
                        and trgt == ancilla
                        and instruction.name[1] == "X"
                    ):
                        stype = PauliBasis.Z
                    else:
                        stype = PauliBasis.U
                    # TODO: handle extended stabilizers differently to be able to detect erroneous stabilizers.
                    # explanation = "A stabilizer can use CX(a,d) or CZ(a,d) in the X-basis and CX(d,a) in the Z-basis."
                    # extra = f"basis:{current.basis}, gate:{instruction.name}, qubits:{ctrl}@{qubit_coordinates[ctrl]},{trgt}@{qubit_coordinates[trgt]}"
                    # raise ValueError(f"Erroneous layout detected. {explanation} [{extra}]")

                    current.interact(
                        moment=ticks,
                        qubit=data,
                        position=qubit_coordinates[data],
                        stabilizer=stype,
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

    def __eq__(self, other):
        if not isinstance(other, Plaquette):
            return False
        else:
            return (
                self.stabilizer_type == other.stabilizer_type
                and self.schedule == other.schedule
            )

    def __hash__(self):
        return hash(
            (
                self.stabilizer_type,
                frozenset((k, v) for k, v in self.__interactions.items()),
            )
        )

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "".join(str(m) if m != -1 else "-" for m in self.schedule)
