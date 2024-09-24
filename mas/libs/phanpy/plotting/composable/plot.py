# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\plot.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/06/2024 11:02 am
#
# Last Modified: 08/19/2024 03:10 pm
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from typing import Iterable, Literal, cast

import bokeh.models as bm
import polars as pl
from typing_extensions import NotRequired, Self, Sequence, Unpack

from mas.libs.phanpy.plotting.composable.glyphs import GlyphSpec
from mas.libs.phanpy.plotting.facet import FacetFilter
from mas.libs.phanpy.plotting.layer.plot import Plot as BasePlot
from mas.libs.phanpy.plotting.layer.plot import PlotConstructorProps
from mas.libs.phanpy.types.typeddict import keysafe_typeddict


class ComposablePlotConstructorProps(PlotConstructorProps):
    glyphs: NotRequired[Sequence[GlyphSpec]]


class Plot(BasePlot):
    def __init__(
        self,
        **props: Unpack[ComposablePlotConstructorProps],
    ) -> None:
        super().__init__(**keysafe_typeddict(props, PlotConstructorProps))
        self._glyphs = [*props.get("glyphs", [])]

    def add(self, *glyph: GlyphSpec | None | Literal[False]) -> Self:
        self_ = self.copy(deep=True)
        self_._glyphs.extend(
            cast(
                Iterable[GlyphSpec],
                filter(lambda _: _ is not None and not False, glyph),
            )
        )
        return self_

    def __call__(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: FacetFilter | None,
    ) -> None:
        for glyph in self._glyphs:
            glyph._draw(
                figure=figure,
                legend=legend,
                data=data,
                facet_filter=facet_filter,
            )
