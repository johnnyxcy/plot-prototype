# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\render.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/15/2024 03:18 pm
#
# Last Modified: 08/27/2024 01:32 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from typing import Literal, TypedDict

import bokeh.models as bm
import polars as pl
from bokeh.core.enums import RenderLevelType
from typing_extensions import NotRequired

from mas.libs.phanpy.plotting.constants import (
    GLYPH_FIELD_TOOLTIPS_COLUMN_NAME,
    RENDERER_TAG,
    GlyphTooltipsTag,
)
from mas.libs.phanpy.plotting.legends import handle_legend_group, handle_legend_label

GlyphLegendType = Literal["label", "group"]


class GlyphLegendSpec(TypedDict):
    legend_type: NotRequired[GlyphLegendType]
    legend_value: NotRequired[str]


def typesafe_glyph_legend(
    legend_label: str | None = None,
    legend_group: str | None = None,
) -> GlyphLegendSpec | None:
    if legend_label is not None and legend_group is not None:
        raise ValueError(
            "Only one of legend_label or legend_group could be provided, not both."
        )

    if legend_group is not None:
        return GlyphLegendSpec(legend_type="group", legend_value=legend_group)

    if legend_label is not None:
        return GlyphLegendSpec(legend_type="label", legend_value=legend_label)

    return None


def update_legend(
    legend_type: GlyphLegendType,
    legend_value: str,
    legend_model: bm.Legend,
    renderer: bm.GlyphRenderer,
) -> None:
    if legend_type == "label":
        handle_legend_label(
            legend_value,
            legend=legend_model,
            glyph_renderer=renderer,
        )

    elif legend_type == "group":
        handle_legend_group(
            legend_value,
            legend=legend_model,
            glyph_renderer=renderer,
        )


def render_glyph(
    data: pl.DataFrame,
    glyph: bm.Glyph,
    figure: bm.Plot,
    name: str | None = None,
    legend: bm.Legend | None = None,
    legend_spec: GlyphLegendSpec | None = None,
    tooltip_template: pl.Expr | None = None,
    level: RenderLevelType = "glyph",
) -> bm.GlyphRenderer:
    tags = [RENDERER_TAG]
    if tooltip_template is not None:
        data = data.with_columns(
            tooltip_template.alias(GLYPH_FIELD_TOOLTIPS_COLUMN_NAME)
        )
        tags.append(GlyphTooltipsTag.FIELD.value)

    source = bm.ColumnDataSource(data.to_dict())
    renderer = figure.add_glyph(
        source,
        glyph=glyph,
        name=name,
        tags=tags,
        level=level,
    )
    if legend is not None and legend_spec is not None:
        update_legend(
            legend_type=legend_spec.get("legend_type", "label"),
            legend_value=legend_spec.get("legend_value", ""),
            legend_model=legend,
            renderer=renderer,
        )
    return renderer
