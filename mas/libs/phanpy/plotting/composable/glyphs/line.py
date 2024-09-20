# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\glyphs\line.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 05:54 pm
#
# Last Modified: 09/12/2024 10:55 am
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################

import bokeh.models as bm
import polars as pl
from typing_extensions import Unpack

from mas.libs.phanpy.plotting.composable.glyphs.abstract import (
    GlyphRenderable,
    GlyphSpec,
)
from mas.libs.phanpy.plotting.field import DataSpec, interpret_data_spec
from mas.libs.phanpy.plotting.props import LineProps
from mas.libs.phanpy.plotting.render import typesafe_glyph_legend
from mas.libs.phanpy.plotting.traits import LineStyleableTrait
from mas.libs.phanpy.types.primitive import NumberLike


class LineGlyphStyles(LineProps):
    pass


class Line(GlyphSpec, LineStyleableTrait[LineGlyphStyles]):
    Styles = LineGlyphStyles

    def __init__(
        self,
        x: DataSpec[NumberLike],
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
        self._x = x
        self._y = y

        self._styles = styles or self.Styles()

    def _draw(self, renderable: GlyphRenderable) -> None:
        data, (x, y) = interpret_data_spec(
            data=renderable.data,
            x=self._x,
            y=self._y,
        )
        default_tooltip_template = pl.concat_str(
            pl.format("{}={}", pl.lit(x), pl.col(x)),
            pl.lit("<br>"),
            pl.format("{}={}", pl.lit(y), pl.col(y)),
        )
        self.render_glyph_with_reducing_props(
            figure=renderable.figure,
            legend=renderable.legend,
            data=data,
            glyph=bm.Line(x=x, y=y),
            props={**self._styles},
            default_tooltip_template=default_tooltip_template,
        )


class VLine(GlyphSpec, LineStyleableTrait[LineGlyphStyles]):
    Styles = LineGlyphStyles

    def __init__(
        self,
        x: DataSpec[NumberLike],
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
        self._styles = styles or self.Styles()

    def _draw(self, renderable: GlyphRenderable) -> None:
        data, (x,) = interpret_data_spec(
            data=renderable.data,
            x=self._x,
        )
        self.render_glyph(
            figure=renderable.figure,
            legend=renderable.legend,
            data=data,
            glyph=bm.VSpan(x=x, **self._styles),
        )


class HLine(GlyphSpec, LineStyleableTrait[LineGlyphStyles]):
    Styles = LineGlyphStyles

    def __init__(
        self,
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

        self._styles = styles or self.Styles()

    def _draw(self, renderable: GlyphRenderable) -> None:
        data, (y,) = interpret_data_spec(
            data=renderable.data,
            y=self._y,
        )
        self.render_glyph(
            figure=renderable.figure,
            legend=renderable.legend,
            data=data,
            glyph=bm.HSpan(y=y, **self._styles),
        )


class Segment(GlyphSpec, LineStyleableTrait[LineGlyphStyles]):
    Styles = LineGlyphStyles

    def __init__(
        self,
        x0: NumberLike,
        y0: NumberLike,
        x1: NumberLike,
        y1: NumberLike,
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
        self._x0 = x0
        self._y0 = y0
        self._x1 = x1
        self._y1 = y1

        self._styles = styles or self.Styles()

    def _draw(self, renderable: GlyphRenderable) -> None:
        self.render_glyph(
            figure=renderable.figure,
            legend=renderable.legend,
            data=pl.DataFrame(
                {
                    "x0": [self._x0],
                    "x1": [self._x1],
                    "y0": [self._y0],
                    "y1": [self._y1],
                }
            ),
            glyph=bm.Segment(
                x0="x0",
                x1="x1",
                y0="y0",
                y1="y1",
                **self._styles,
            ),
        )


class Ray(GlyphSpec, LineStyleableTrait[LineGlyphStyles]):
    Styles = LineGlyphStyles

    def __init__(
        self,
        x: NumberLike,
        y: NumberLike,
        degree: NumberLike = 0,
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
        self._y = y
        self._degree = degree

        self._styles = styles or self.Styles()

    def _draw(self, renderable: GlyphRenderable) -> None:
        self.render_glyph(
            figure=renderable.figure,
            legend=renderable.legend,
            data=pl.DataFrame(
                {
                    "x": [self._x],
                    "y": [self._y],
                    "angle": [self._degree],
                }
            ),
            glyph=bm.Ray(
                x="x",
                y="y",
                angle="angle",
                angle_units="deg",
                **self._styles,
            ),
        )
