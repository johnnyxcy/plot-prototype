# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\glyphs\step.py
#
# Author: 姚泽 <ze.yao@drugchina.net>
#
# File Created: 09/09/2024 02:24 pm
#
# Last Modified: 09/09/2024 02:38 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from typing import Literal

import bokeh.models as bm
import polars as pl
from typing_extensions import NotRequired, Unpack

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

StepModeType = Literal["before", "after", "center"]


class StepGlyphStyles(LineProps):
    mode: NotRequired[StepModeType]


class Step(GlyphSpec, LineStyleableTrait[StepGlyphStyles]):
    Styles = StepGlyphStyles

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
            glyph=bm.Step(x=x, y=y),
            props={**self._styles},
            level=level,
            default_tooltip_template=default_tooltip_template,
        )
