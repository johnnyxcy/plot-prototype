# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\glyphs\text.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/19/2024 08:17 am
#
# Last Modified: 08/23/2024 02:44 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from __future__ import annotations

from typing import Any, Literal

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
    interpret_data_spec,
    replace_field_props,
)
from mas.libs.phanpy.plotting.props import JitterProps, TextProps
from mas.libs.phanpy.plotting.render import typesafe_glyph_legend
from mas.libs.phanpy.plotting.traits import TextStyleableTrait
from mas.libs.phanpy.types.primitive import NumberLike, TextLike


class TextGlyphStyles(
    TextProps,
):
    jitter: NotRequired[JitterProps]
    x_offset: NotRequired[NumberLike]
    y_offset: NotRequired[NumberLike]
    anchor: NotRequired[str]


TextTypesettingType = Literal["plaintext", "tex", "mathml"]


class Text(
    GlyphSpec,
    TextStyleableTrait[TextGlyphStyles],
):
    Styles = TextGlyphStyles

    def __init__(
        self,
        x: DataSpec[NumberLike],
        y: DataSpec[NumberLike],
        text: DataSpec[TextLike],
        # angle: DataSpec[NumberLike],
        # x_offset: DataSpec[NumberLike],
        # y_offset: DataSpec[NumberLike],
        typeset: TextTypesettingType = "plaintext",
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
        self._text = text
        # self._angle = angle
        # self._x_offset = x_offset
        # self._y_offset = y_offset
        self._typeset: TextTypesettingType = typeset
        self._styles = styles or self.Styles()

    @classmethod
    def TeX(
        cls,
        x: DataSpec[NumberLike],
        y: DataSpec[NumberLike],
        text: DataSpec[TextLike],
        name: str | None = None,
        *,
        legend_label: str | None = None,
        legend_group: str | None = None,
        **styles: Unpack[Styles],
    ) -> Text:
        return Text(
            x=x,
            y=y,
            text=text,
            typeset="tex",
            name=name,
            legend_label=legend_label,
            legend_group=legend_group,
            **styles,
        )

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
        data, (x, y, text) = interpret_data_spec(
            data=data,
            x=self._x,
            y=self._y,
            text=self._text,
        )
        styles: dict[str, Any] = {**self._styles}

        jitter_styles: JitterProps = styles.pop("jitter", JitterProps())
        styles, data = replace_field_props(styles, data=data)

        if isinstance(figure.x_scale, bm.CategoricalScale):
            x = BokehField(
                x,
                bm.Jitter(
                    width=jitter_styles.get("width", 0.5),
                    mean=jitter_styles.get("mean", 0),
                    distribution=jitter_styles.get("distribution", "uniform"),
                    range=figure.x_range,
                ),
            )

        if isinstance(figure.y_scale, bm.CategoricalScale):
            y = BokehField(
                y,
                bm.Jitter(
                    width=jitter_styles.get("width", 0.5),
                    mean=jitter_styles.get("mean", 0),
                    distribution=jitter_styles.get("distribution", "uniform"),
                    range=figure.y_range,
                ),
            )
        if self._typeset == "plaintext":
            glyph = bm.Text(x=x, y=y, text=text)
        elif self._typeset == "tex":
            glyph = bm.TeXGlyph(x=x, y=y, text=text)
        elif self._typeset == "mathml":
            glyph = bm.MathMLGlyph(x=x, y=y, text=text)
        else:
            raise ValueError(f"Invalid typeset {self._typeset}")

        self.render_glyph(
            figure=figure,
            legend=legend,
            data=data,
            facet_filter=facet_filter,
            glyph=glyph,
            props={**styles},
            level=level,
        )
