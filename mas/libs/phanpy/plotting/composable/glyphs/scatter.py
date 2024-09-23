# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\glyphs\scatter.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 05:55 pm
#
# Last Modified: 09/12/2024 02:55 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from typing import Any

import bokeh.models as bm
import polars as pl
from bokeh.core.property.vectorization import Field as BokehField
from typing_extensions import NotRequired, Self, Unpack

from mas.libs.phanpy.plotting.composable.glyphs.abstract import (
    GlyphSpec,
    RenderLevelType,
)
from mas.libs.phanpy.plotting.field import (
    DataSpec,
    get_field_props,
    interpret_data_spec,
    replace_field_props,
)
from mas.libs.phanpy.plotting.props import (
    FillProps,
    JitterProps,
    LineProps,
    MarkerProps,
)
from mas.libs.phanpy.plotting.render import typesafe_glyph_legend
from mas.libs.phanpy.plotting.traits import (
    FillStyleableTrait,
    LineStyleableTrait,
    MarkerStylableTrait,
)
from mas.libs.phanpy.types.primitive import NumberLike


class ScatterGlyphStyles(
    MarkerProps,
    FillProps,
    LineProps,
):
    jitter: NotRequired[JitterProps]


class Scatter(
    GlyphSpec,
    LineStyleableTrait[ScatterGlyphStyles],
    FillStyleableTrait[ScatterGlyphStyles],
    MarkerStylableTrait[ScatterGlyphStyles],
):
    Styles = ScatterGlyphStyles

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

    def with_jitter(self, **props: Unpack[JitterProps]) -> Self:
        self_ = self.copy()
        jitter_styles = self_._styles.get("jitter", {})
        jitter_styles.update(**props)
        self_._styles["jitter"] = jitter_styles
        return self_

    def _draw(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: pl.Expr | None,
        level: RenderLevelType = "glyph",
    ) -> None:
        data, (x, y) = interpret_data_spec(
            data=data,
            x=self._x,
            y=self._y,
        )
        default_tooltip_template = pl.concat_str(
            pl.lit(f"{x}="), pl.col(x), pl.lit("<br>"), pl.lit(f"{y}="), pl.col(y)
        )
        styles: dict[str, Any] = {**self._styles}

        jitter_styles: JitterProps = styles.pop("jitter", None)
        field_props = get_field_props(styles)
        styles, data = replace_field_props(styles, data=data)
        fill_color = styles.get("fill_color", None)
        line_color = styles.get("line_color", None)
        if fill_color and line_color is None:
            styles["line_color"] = fill_color

        if (
            isinstance(figure.x_scale, bm.CategoricalScale)
            and jitter_styles is not None
        ):
            x = BokehField(
                x,
                bm.Jitter(
                    width=jitter_styles.get("width", 0.5),
                    mean=jitter_styles.get("mean", 0),
                    distribution=jitter_styles.get("distribution", "uniform"),
                    range=figure.x_range,
                ),
            )

        if (
            isinstance(figure.y_scale, bm.CategoricalScale)
            and jitter_styles is not None
        ):
            y = BokehField(
                y,
                bm.Jitter(
                    width=jitter_styles.get("width", 0.5),
                    mean=jitter_styles.get("mean", 0),
                    distribution=jitter_styles.get("distribution", "uniform"),
                    range=figure.y_range,
                ),
            )

        glyph = bm.Scatter(x=x, y=y, **styles)
        for field_spec_constructor in field_props.values():
            default_tooltip_template = pl.concat_str(
                default_tooltip_template,
                pl.lit("<br>"),
                pl.lit(f"{field_spec_constructor.column_name}="),
                pl.col(field_spec_constructor.column_name),
            )

        self.render_glyph(
            figure=figure,
            legend=legend,
            data=data,
            facet_filter=facet_filter,
            glyph=glyph,
            props=styles,
            level=level,
            default_tooltip_template=default_tooltip_template,
        )
