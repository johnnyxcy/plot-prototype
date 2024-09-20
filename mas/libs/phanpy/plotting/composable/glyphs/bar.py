# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\glyphs\bar.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/14/2024 03:22 pm
#
# Last Modified: 08/19/2024 03:28 pm
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
import bokeh.models as bm
from typing_extensions import Unpack

from mas.libs.phanpy.plotting.composable.glyphs.abstract import GlyphRenderable, GlyphSpec
from mas.libs.phanpy.plotting.field import DataSpec, interpret_data_spec, replace_field_props
from mas.libs.phanpy.plotting.props import FillProps, LineProps
from mas.libs.phanpy.plotting.render import typesafe_glyph_legend
from mas.libs.phanpy.plotting.traits import FillStyleableTrait, LineStyleableTrait
from mas.libs.phanpy.types.primitive import NumberLike, TextLike


class BarGlyphStyles(
    FillProps,
    LineProps,
):
    pass


class VBar(
    GlyphSpec,
    FillStyleableTrait[BarGlyphStyles],
    LineStyleableTrait[BarGlyphStyles],
):
    Styles = BarGlyphStyles

    def __init__(
        self,
        x: DataSpec[TextLike],
        top: DataSpec[NumberLike],
        bottom: DataSpec[NumberLike],
        width: NumberLike = 1,
        name: str | None = None,
        *,
        legend_label: str | None = None,
        legend_group: str | None = None,
        **styles: Unpack[Styles],
    ) -> None:
        super().__init__(
            name=name,
            legend=typesafe_glyph_legend(
                legend_label=legend_label,
                legend_group=legend_group,
            ),
        )
        self._x = x
        self._width = width
        self._top = top
        self._bottom = bottom
        self._styles = styles or self.Styles()

    def _draw(self, renderable: GlyphRenderable) -> None:
        data, (x, top, bottom) = interpret_data_spec(
            data=renderable.data,
            x=self._x,
            top=self._top,
            bottom=self._bottom,
        )

        styles_d = {"fill_alpha": 0.95, **self._styles}
        (styles, data) = replace_field_props(styles_d, data=data)

        glyph = bm.VBar(
            x=x,
            top=top,
            bottom=bottom,
            width=self._width,
            **styles,
        )
        self.render_glyph(
            figure=renderable.figure,
            legend=renderable.legend,
            data=data,
            glyph=glyph,
            level=renderable.level,
        )


class HBar(
    GlyphSpec,
    FillStyleableTrait[BarGlyphStyles],
    LineStyleableTrait[BarGlyphStyles],
):
    Styles = BarGlyphStyles

    def __init__(
        self,
        y: DataSpec[TextLike],
        left: DataSpec[NumberLike],
        right: DataSpec[NumberLike],
        height: NumberLike = 1,
        name: str | None = None,
        *,
        legend_label: str | None = None,
        legend_group: str | None = None,
        **styles: Unpack[Styles],
    ) -> None:
        super().__init__(
            name=name,
            legend=typesafe_glyph_legend(
                legend_label=legend_label,
                legend_group=legend_group,
            ),
        )
        self._y = y
        self._height = height
        self._left = left
        self._right = right
        self._styles = styles or self.Styles()

    def _draw(self, renderable: GlyphRenderable) -> None:
        data, (y, left, right) = interpret_data_spec(
            data=renderable.data,
            y=self._y,
            left=self._left,
            right=self._right,
        )
        styles_d = {"fill_alpha": 0.95, **self._styles}
        (styles, data) = replace_field_props(styles_d, data=data)
        glyph = bm.HBar(
            y=y,
            left=left,
            right=right,
            height=self._height,
            **styles,
        )
        self.render_glyph(
            figure=renderable.figure,
            legend=renderable.legend,
            data=data,
            glyph=glyph,
        )
