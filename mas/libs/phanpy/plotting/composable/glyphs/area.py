# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\glyphs\area.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 05:56 pm
#
# Last Modified: 08/19/2024 04:21 pm
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
import bokeh.models as bm
import polars as pl
from typing_extensions import Unpack

from mas.libs.phanpy.plotting.composable.glyphs.abstract import (
    GlyphSpec,
    RenderLevelType,
)
from mas.libs.phanpy.plotting.field import (
    DataSpec,
    interpret_data_spec,
)
from mas.libs.phanpy.plotting.props import FillProps, LineProps
from mas.libs.phanpy.plotting.render import typesafe_glyph_legend
from mas.libs.phanpy.plotting.traits import FillStyleableTrait, LineStyleableTrait
from mas.libs.phanpy.types.primitive import NumberLike


class RectangleGlyphStyles(FillProps, LineProps):
    pass


class Rectangle(
    GlyphSpec,
    FillStyleableTrait[RectangleGlyphStyles],
    LineStyleableTrait[RectangleGlyphStyles],
):
    Styles = RectangleGlyphStyles

    # 虽然这个叫 Rectangle，但是我们倾向于使用 Quad (left, top, right, bottom)，而不是 Rect (x, y, height, width)

    def __init__(
        self,
        left: DataSpec[NumberLike],
        right: DataSpec[NumberLike],
        top: DataSpec[NumberLike],
        bottom: DataSpec[NumberLike],
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
        self._left = left
        self._right = right
        self._top = top
        self._bottom = bottom
        self._styles = styles or self.Styles()

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: pl.Expr | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        (
            data,
            (
                left,
                right,
                top,
                bottom,
            ),
        ) = interpret_data_spec(
            data=data,
            left=self._left,
            right=self._right,
            top=self._top,
            bottom=self._bottom,
        )

        self.render_glyph(
            figure=figure,
            legend=legend,
            data=data,
            facet_filter=facet_filter,
            glyph=bm.Quad(
                left=left,
                right=right,
                top=top,
                bottom=bottom,
            ),
            level=level,
            props={"fill_alpha": 0.95, **self._styles},
        )


class VAreaGlyphStyles(FillProps):
    pass


class VArea(
    GlyphSpec,
    FillStyleableTrait[VAreaGlyphStyles],
):
    Styles = VAreaGlyphStyles

    def __init__(
        self,
        x: DataSpec[NumberLike],
        y1: DataSpec[NumberLike],
        y2: DataSpec[NumberLike],
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
        self._y1 = y1
        self._y2 = y2
        self._styles = styles or self.Styles()

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: pl.Expr | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        (
            data,
            (
                x,
                y1,
                y2,
            ),
        ) = interpret_data_spec(
            data=data,
            x=self._x,
            y1=self._y1,
            y2=self._y2,
        )
        self.render_glyph(
            figure=figure,
            legend=legend,
            data=data,
            glyph=bm.VArea(
                x=x,
                y1=y1,
                y2=y2,
            ),
            facet_filter=facet_filter,
            props={"fill_alpha": 0.95, **self._styles},
            level=level,
            default_tooltip_template=pl.concat_str(
                pl.format("{}={}", pl.lit(x), pl.col(x)),
                pl.lit("<br>"),
                pl.format("{}={}", pl.lit(y1), pl.col(y1)),
                pl.lit("<br>"),
                pl.format("{}={}", pl.lit(y2), pl.col(y2)),
            ),
        )


class HAreaGlyphStyles(FillProps):
    pass


class HArea(
    GlyphSpec,
    FillStyleableTrait[HAreaGlyphStyles],
):
    Styles = HAreaGlyphStyles

    def __init__(
        self,
        x1: DataSpec[NumberLike],
        x2: DataSpec[NumberLike],
        y: DataSpec[NumberLike],
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
        self._x1 = x1
        self._x2 = x2
        self._styles = styles or self.Styles()

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: pl.Expr | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        (
            data,
            (
                x1,
                x2,
                y,
            ),
        ) = interpret_data_spec(
            data=data,
            x1=self._x1,
            x2=self._x2,
            y=self._y,
        )
        self.render_glyph(
            figure=figure,
            legend=legend,
            level=level,
            data=data,
            facet_filter=facet_filter,
            glyph=bm.HArea(
                x1=x1,
                x2=x2,
                y=y,
            ),
            props={"fill_alpha": 0.95, **self._styles},
            default_tooltip_template=pl.concat_str(
                pl.format("{}={}", pl.lit(x1), pl.col(x1)),
                pl.lit("<br>"),
                pl.format("{}={}", pl.lit(x2), pl.col(x2)),
                pl.lit("<br>"),
                pl.format("{}={}", pl.lit(y), pl.col(y)),
            ),
        )
