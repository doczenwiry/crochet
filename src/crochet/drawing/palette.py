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
from enum import Enum

from PIL import ImageColor

from crochet.core.common import PauliBasis, Qubit
from crochet.core.plaquette import Plaquette

ZX_PALETTE = {
    PauliBasis.U: "lightgray",
    PauliBasis.X: "#CF4040",
    PauliBasis.Y: "#40CF40",
    PauliBasis.Z: "#4040CF",
}


class Palette(Enum):
    ZX = 0
    SCHEDULES = 1

    @staticmethod
    def make(stabilizers, style: Palette):
        if style == Palette.ZX:
            return PaletteZx()
        else:
            return PaletteSchedules(stabilizers)


class PaletteZx:
    def __init__(self):
        self.__palette = ZX_PALETTE

    def get_color(self, plaquette: Plaquette) -> str:
        return self.__palette[plaquette.stabilizer_type]


class PaletteSchedules:
    def __init__(self, stabilizers: dict[Qubit, Plaquette]):
        self.__palette = {}
        collected = set()
        for s in stabilizers.values():
            print(f"Stabilizer {s.stabilizer_type}/{s.schedule} : {hash(s)}")
            collected.add(s)
        n = len(collected)
        print(f"Collected {n} plaquette types.")

        saturation = 80
        value = 90
        for i, plq in enumerate(collected):
            hue = int(360 * i / n)
            rgb = ImageColor.getrgb(f"hsv({hue},{saturation}%,{value}%)")
            self.__palette[plq] = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def get_color(self, plaquette: Plaquette) -> str:
        return self.__palette[plaquette]
