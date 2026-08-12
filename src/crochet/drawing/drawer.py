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

from collections import Counter, defaultdict

from PIL import Image, ImageDraw, ImageFont, ImageOps

from crochet.core.common import Qubit
from crochet.core.plaquette import Plaquette
from crochet.drawing.palette import Palette
from crochet.utils.geometry import Geometry


class Drawer:
    __UNIT = 64
    __RADIUS = 0.3125

    @staticmethod
    def __make_shape(plaquette: Plaquette):
        x, y = plaquette.location
        return [
            ((x + dx) * Drawer.__UNIT, (y + dy) * Drawer.__UNIT)
            for _, dx, dy in sorted(
                (Geometry.theta(dx, dy), dx, dy) for dx, dy in plaquette.corners
            )
        ]

    @staticmethod
    def __make_chord(plaquette: Plaquette):
        x, y = plaquette.location
        (x0, y0), (x1, y1) = plaquette.corners

        if x0 == x1:
            y0, y1 = min(y0, y1), max(y0, y1)
            side = (y1 - y0) / 2.0
            points = [x + x0 - side, y + y0, x + x0 + side, y + y1]
            start, final = (270, 90) if x0 < 0 else (90, 270)
        else:  # y0 == y1
            x0, x1 = min(x0, x1), max(x0, x1)
            side = (x1 - x0) / 2.0
            points = [x + x0, y + y0 - side, x + x1, y + y0 + side]
            start, final = (0, 180) if y0 < 0 else (180, 0)

        return [p * Drawer.__UNIT for p in points], start, final

    @staticmethod
    def draw(
        rows: int,
        cols: int,
        stabilizers: dict[Qubit, Plaquette],
        qubit_at_location: dict[tuple[float, float], Qubit],
        fontsize: int,
        style: Palette,
        savefile: str | None = None,
    ):
        font = ImageFont.truetype(
            "/System/Library/Fonts/Menlo.ttc", size=fontsize, index=1
        )
        image = Image.new("RGB", (cols * Drawer.__UNIT, rows * Drawer.__UNIT), "gray")
        drawer = ImageDraw.Draw(image)

        palette = Palette.make(stabilizers, style=style)

        earliest = min(stabilizers.values(), key=lambda plq: plq.start)

        touched: dict[tuple[float, float], Counter] = defaultdict(Counter)
        for plaquette in stabilizers.values():
            if len(plaquette.interactions) < 2:
                continue

            color = palette.get_color(plaquette)

            if len(plaquette.interactions) == 2:
                drawer.chord(*Drawer.__make_chord(plaquette), fill=color)
            else:  # len(plaquette.interactions) >= 3
                drawer.polygon(Drawer.__make_shape(plaquette), fill=color)

            px, py = plaquette.location
            for (dx, dy), moment in plaquette.interactions.items():
                qubit = px + dx, py + dy
                touched[qubit][moment] += 1

        for (qx, qy), counter in touched.items():
            if any(count > 1 for _, count in counter.items()):
                radius = Drawer.__RADIUS
                bounding = [
                    pos * Drawer.__UNIT
                    for pos in [qx - radius, qy - radius, qx + radius, qy + radius]
                ]
                drawer.ellipse(bounding, fill="#FFFF00")

        for plaquette in stabilizers.values():
            px, py = plaquette.location
            for corner in plaquette.corners:
                moment = plaquette.interactions[corner]
                cx, cy = corner
                position = (
                    (px + 0.70 * cx) * Drawer.__UNIT,
                    (py + 0.70 * cy) * Drawer.__UNIT,
                )
                drawer.text(
                    position,
                    text=str(moment - earliest.start),
                    fill="black",
                    anchor="mm",
                    font=font,
                )

            interactions_p = plaquette.interactions

            plaquette_r = stabilizers.get(
                qubit_at_location.get((px + 1.0, py), -1), None
            )
            if plaquette_r:
                interactions_r = plaquette_r.interactions

                intersection = list(
                    set(interactions_p.keys()).intersection(interactions_r.keys())
                )
                if len(intersection) == 2:
                    q0, q1 = intersection
                    if (interactions_p[q0] < interactions_r[q0]) ^ (
                        interactions_p[q1] < interactions_r[q1]
                    ):
                        label_position = (
                            (px + 0.5) * Drawer.__UNIT,
                            py * Drawer.__UNIT,
                        )
                        drawer.text(
                            label_position,
                            text="X",
                            fill="yellow",
                            anchor="mm",
                            font=font,
                        )

            plaquette_b = stabilizers.get(
                qubit_at_location.get((px, py + 1.0), -1), None
            )
            if plaquette_b:
                interactions_b = plaquette_b.interactions

                intersection = list(
                    set(interactions_p.keys()).intersection(interactions_b.keys())
                )
                if len(intersection) == 2:
                    q0, q1 = intersection
                    if (interactions_p[q0] < interactions_b[q0]) ^ (
                        interactions_p[q1] < interactions_b[q1]
                    ):
                        label_position = (
                            px * Drawer.__UNIT,
                            (py + 0.5) * Drawer.__UNIT,
                        )
                        drawer.text(
                            label_position,
                            text="X",
                            fill="yellow",
                            anchor="mm",
                            font=font,
                        )

        image = ImageOps.expand(image, border=Drawer.__UNIT, fill="gray")

        if savefile:
            image.save(savefile)
        else:
            image.show()
