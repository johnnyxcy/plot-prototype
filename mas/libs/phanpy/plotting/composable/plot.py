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
from typing_extensions import NotRequired, Self, Sequence, Unpack

from mas.libs.phanpy.plotting.base import BasePlot, BasePlotConstructorProps
from mas.libs.phanpy.plotting.composable.glyphs import GlyphSpec
from mas.libs.phanpy.plotting.composable.renderable import GlyphRenderable
from mas.libs.phanpy.types.typeddict import keysafe_typeddict


class ComposablePlotConstructorProps(BasePlotConstructorProps):
    glyphs: NotRequired[Sequence[GlyphSpec]]


class Plot(BasePlot):
    def __init__(
        self,
        **props: Unpack[ComposablePlotConstructorProps],
    ) -> None:
        super().__init__(**keysafe_typeddict(props, BasePlotConstructorProps))
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

    def _do_render(self, renderable: GlyphRenderable) -> None:
        for glyph in self._glyphs:
            glyph._draw(renderable)

    def _render(self, figure: bm.Plot, legend: bm.Legend) -> None:
        self._do_render(
            GlyphRenderable(
                figure=figure,
                legend=legend,
                data=self._data,
            )
        )
