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
    GlyphSpec,
    RenderLevelType,
)
from mas.libs.phanpy.plotting.field import DataSpec, interpret_data_spec
from mas.libs.phanpy.plotting.layer.plot import FacetFilter
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
        group: str | None = None,
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
        self._group = group
        self._styles = styles or self.Styles()

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: FacetFilter | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        data, (x, y) = interpret_data_spec(
            data=data,
            x=self._x,
            y=self._y,
        )

        if self._group is not None:
            # use multiline
            data = (
                data.group_by(self._group)
                .agg(pl.all())
                .explode(pl.all().exclude(self._group, x, y))
            )
            glyph = bm.MultiLine(xs=x, ys=y)
            default_tooltip_template = pl.concat_str(
                pl.format("{}={}", pl.lit(self._group), pl.col(self._group)),
            )
        else:
            glyph = bm.Line(x=x, y=y)
            default_tooltip_template = pl.concat_str(
                pl.format("{}={}", pl.lit(x), pl.col(x)),
                pl.lit("<br>"),
                pl.format("{}={}", pl.lit(y), pl.col(y)),
            )

        self.render_glyph(
            figure=figure,
            legend=legend,
            data=data,
            facet_filter=facet_filter,
            level=level,
            glyph=glyph,
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

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: FacetFilter | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        data, (x,) = interpret_data_spec(
            data=data,
            x=self._x,
        )
        self.render_glyph(
            figure=figure,
            legend=legend,
            data=data,
            facet_filter=facet_filter,
            level=level,
            props={**self._styles},
            glyph=bm.VSpan(x=x),
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

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: FacetFilter | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        data, (y,) = interpret_data_spec(
            data=data,
            y=self._y,
        )
        self.render_glyph(
            figure=figure,
            legend=legend,
            data=data,
            level=level,
            facet_filter=facet_filter,
            glyph=bm.HSpan(y=y),
            props={**self._styles},
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

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: FacetFilter | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        self.render_glyph(
            figure=figure,
            legend=legend,
            data=pl.DataFrame(
                {
                    "x0": [self._x0],
                    "x1": [self._x1],
                    "y0": [self._y0],
                    "y1": [self._y1],
                }
            ),
            facet_filter=None,
            glyph=bm.Segment(
                x0="x0",
                x1="x1",
                y0="y0",
                y1="y1",
            ),
            level=level,
            props={**self._styles},
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

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: FacetFilter | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        self.render_glyph(
            figure=figure,
            legend=legend,
            data=pl.DataFrame(
                {
                    "x": [self._x],
                    "y": [self._y],
                    "angle": [self._degree],
                }
            ),
            facet_filter=None,
            glyph=bm.Ray(
                x="x",
                y="y",
                angle="angle",
                angle_units="deg",
            ),
            level=level,
            props={**self._styles},
        )
