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


class Geometry:
    # Thanks, Claude.AI (August 2026)
    @staticmethod
    def theta(px: float, py: float) -> float:
        """Approximation to avoid expensive arctan(..). Acceptable within ~5 degrees."""
        adx, ady = abs(px), abs(py)

        angle: float
        if adx > ady:
            angle = (ady / adx) * math.pi / 4.0
        else:
            angle = (math.pi / 2.0) - (adx / ady) * (math.pi / 4.0)

        if px < 0:
            angle = math.pi - angle
        if py < 0:
            angle = 2.0 * math.pi - angle

        return angle
