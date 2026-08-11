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


from PIL import Image, ImageDraw, ImageFont, ImageOps

from crochet.core.common import Qubit
from crochet.core.plaquette import Plaquette, StabilizerType


class Drawer:
    __UNIT = 64

    @staticmethod
    def __make_shape(position):
        x, y = position
        return [
            ((x + dx) * Drawer.__UNIT, (y + dy) * Drawer.__UNIT)
            for dx, dy in [(-0.5, -0.5), (+0.5, -0.5), (+0.5, +0.5), (-0.5, +0.5)]
        ]

    @staticmethod
    def __make_chord(position, base_shape, scale):
        x, y = position
        x0, y0, x1, y1 = base_shape
        return [(x0 + x) * scale, (y0 + y) * scale, (x1 + x) * scale, (y1 + y) * scale]

    @staticmethod
    def draw(
        rows: int,
        cols: int,
        stabilizers: dict[Qubit, Plaquette],
        savefile: str | None = None,
    ):
        image = Image.new("RGB", (cols * Drawer.__UNIT, rows * Drawer.__UNIT), "gray")
        drawer = ImageDraw.Draw(image)
        font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf", size=16
        )

        earliest = min(stabilizers.values(), key=lambda plq: plq.start)

        for plaquette in stabilizers.values():
            if len(plaquette.interactions) == 0:
                continue

            color = (
                "#CF4040"
                if plaquette.stabilizer_type == StabilizerType.X
                else "#4040CF"
            )
            drawer.polygon(
                Drawer.__make_shape(plaquette.location),
                fill=color,
                outline="black",
                width=3,
            )

            px, py = plaquette.location
            for corner in [(-0.5, -0.5), (+0.5, -0.5), (+0.5, +0.5), (-0.5, +0.5)]:
                if corner not in plaquette.interactions:
                    continue

                moment = plaquette.interactions[corner]
                cx, cy = corner
                drawer.text(
                    (
                        (px + 0.65 * cx) * Drawer.__UNIT,
                        (py + 0.65 * cy) * Drawer.__UNIT,
                    ),
                    text=str(moment - earliest.start),
                    fill="black",
                    anchor="mm",
                    font=font,
                )

        image = ImageOps.expand(image, border=Drawer.__UNIT, fill="gray")

        if savefile:
            image.save(savefile)
        else:
            image.show()
