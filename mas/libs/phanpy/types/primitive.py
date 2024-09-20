from typing import Collection

from annotated_types import Interval
from typing_extensions import Annotated

Integer = int
NumberLike = int | float
TextLike = str
IntegerCollection = Collection[Integer]
NumberLikeCollection = Collection[NumberLike]
TextLikeCollection = Collection[TextLike]

ScalarLike = NumberLike | TextLike
VectorLike = NumberLikeCollection | TextLikeCollection
Percentile = Annotated[float, Interval(0, 1)]
