from annotated_types import Interval
from typing_extensions import Annotated

RGBTuple = tuple[int, int, int] | tuple[int, int, int, float]
ColorLike = str | RGBTuple
Alpha = Annotated[float, Interval(0, 1)]
Palette = tuple[ColorLike, ...]
HexPalette = tuple[str, ...]
