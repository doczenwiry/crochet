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
import math
from collections import Counter, defaultdict
from typing import ClassVar

from PIL import Image, ImageDraw, ImageFont, ImageOps

from crochet.core.common import PauliBasis, Qubit
from crochet.core.plaquette import Plaquette


class Drawer:
    __FONT = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size=16, index=1)
    __UNIT = 64
    __RADIUS = 0.3125
    __COLORS: ClassVar[dict[PauliBasis, str]] = {
        PauliBasis.U: "lightgray",
        PauliBasis.X: "#CF4040",
        PauliBasis.Y: "#40CF40",
        PauliBasis.Z: "#4040CF",
    }

    # Thanks, Claude.AI (August 2026)
    @staticmethod
    def __theta(dx: float, dy: float) -> float:
        adx, ady = abs(dx), abs(dy)

        angle: float
        if adx > ady:
            angle = (ady / adx) * math.pi / 4.0
        else:
            angle = (math.pi / 2.0) - (adx / ady) * (math.pi / 4.0)

        if dx < 0:
            angle = math.pi - angle
        if dy < 0:
            angle = 2.0 * math.pi - angle

        return angle

    @staticmethod
    def __make_shape(plaquette: Plaquette):
        x, y = plaquette.location
        return [
            ((x + dx) * Drawer.__UNIT, (y + dy) * Drawer.__UNIT)
            for _, dx, dy in sorted(
                (Drawer.__theta(dx, dy), dx, dy) for dx, dy in plaquette.corners
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
        savefile: str | None = None,
    ):
        image = Image.new("RGB", (cols * Drawer.__UNIT, rows * Drawer.__UNIT), "gray")
        drawer = ImageDraw.Draw(image)

        earliest = min(stabilizers.values(), key=lambda plq: plq.start)

        touched: dict[tuple[float, float], Counter] = defaultdict(Counter)
        for plaquette in stabilizers.values():
            if len(plaquette.interactions) < 2:
                continue

            color = Drawer.__COLORS[plaquette.stabilizer_type]

            if len(plaquette.interactions) == 2:
                points, start, final = Drawer.__make_chord(plaquette)
                drawer.chord(xy=points, start=start, end=final, fill=color)
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
                    font=Drawer.__FONT,
                )

            pschedule = plaquette.schedule

            plaquette_r = stabilizers.get(
                qubit_at_location.get((px + 1.0, py), -1), None
            )
            if plaquette_r:
                rschedule = plaquette_r.schedule

                if (
                    pschedule[1] == -1
                    or pschedule[3] == -1
                    or rschedule[0] == -1
                    or rschedule[2] == -1
                ):
                    continue

                if (pschedule[1] < rschedule[0]) ^ (pschedule[3] < rschedule[2]):
                    label_position = ((px + 0.5) * Drawer.__UNIT, py * Drawer.__UNIT)
                    drawer.text(
                        label_position,
                        text="X",
                        fill="yellow",
                        anchor="mm",
                        font=Drawer.__FONT,
                    )

            plaquette_b = stabilizers.get(
                qubit_at_location.get((px, py + 1.0), -1), None
            )
            if plaquette_b:
                bschedule = plaquette_b.schedule

                if (
                    pschedule[2] == -1
                    or pschedule[3] == -1
                    or bschedule[0] == -1
                    or bschedule[1] == -1
                ):
                    continue

                if (pschedule[2] < bschedule[0]) ^ (pschedule[3] < bschedule[1]):
                    label_position = (px * Drawer.__UNIT, (py + 0.5) * Drawer.__UNIT)
                    drawer.text(
                        label_position,
                        text="X",
                        fill="yellow",
                        anchor="mm",
                        font=Drawer.__FONT,
                    )

        image = ImageOps.expand(image, border=Drawer.__UNIT, fill="gray")

        if savefile:
            image.save(savefile)
        else:
            image.show()
