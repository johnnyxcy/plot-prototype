# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\factor.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 08:56 am
#
# Last Modified: 09/06/2024 10:49 am
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from typing import Any, Iterable, Sequence

import polars as pl
from bokeh.core.enums import MarkerType, MarkerTypeType

from mas.libs.phanpy.plotting.field import (
    DelegateFieldSpecConstructor,
    FactorMapTransformFieldSpec,
)
from mas.libs.phanpy.plotting.palette import NamedPaletteType, use_palette
from mas.libs.phanpy.types.color import ColorLike


def color_map(
    factors: Iterable[Any],
    palette: NamedPaletteType
    | tuple[NamedPaletteType, NamedPaletteType]
    | Sequence[ColorLike]
    | None = None,
) -> dict[Any, ColorLike]:
    factors = [*factors]
    n = len(factors)
    palette_values = use_palette(n=n, palette=palette)
    return {from_: to_ for (from_, to_) in zip(factors, palette_values, strict=True)}


def factor_cmap(
    column_name: str,
    palette: NamedPaletteType
    | tuple[NamedPaletteType, NamedPaletteType]
    | Sequence[ColorLike]
    | None = None,
) -> DelegateFieldSpecConstructor[ColorLike]:
    _palette = palette
    transformed_column_name = f"mas.plotting.factor_cmap.{column_name}"

    def constructor(data: pl.DataFrame) -> FactorMapTransformFieldSpec[ColorLike]:
        nonlocal _palette
        factors = data[column_name].unique().sort()
        mapper = color_map(factors, palette=palette)

        return FactorMapTransformFieldSpec(
            column_name=column_name,
            transformed_column_name=transformed_column_name,
            mapper=mapper,
        )

    return DelegateFieldSpecConstructor(
        column_name=column_name,
        constructor=constructor,
    )


def factor_marker(
    column_name: str,
    markers: Sequence[MarkerTypeType] | None = None,
) -> DelegateFieldSpecConstructor[MarkerTypeType]:
    _markers = markers
    transformed_column_name = f"mas.plotting.factor_marker.{column_name}"

    def constructor(data: pl.DataFrame) -> FactorMapTransformFieldSpec[MarkerTypeType]:
        nonlocal _markers
        factors = data[column_name].unique().sort()
        if _markers is None:
            values = MarkerType._values
            marker_index = -1
            _markers = []
            for i in range(len(factors)):
                if i >= len(MarkerType):
                    marker_index = 0
                else:
                    marker_index += 1
                _markers.append(values[marker_index])
        return FactorMapTransformFieldSpec(
            column_name=column_name,
            transformed_column_name=transformed_column_name,
            mapper={from_: to_ for (from_, to_) in zip(factors, _markers, strict=True)},
        )

    return DelegateFieldSpecConstructor(
        column_name=column_name,
        constructor=constructor,
    )
