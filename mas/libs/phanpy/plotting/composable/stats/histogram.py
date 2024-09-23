# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\stats\histogram.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/08/2024 10:13 am
#
# Last Modified: 09/13/2024 08:57 am
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypedDict

import bokeh.models as bm
import numpy as np
import polars as pl
from polars._typing import PolarsDataType
from typing_extensions import NotRequired, Self, Unpack

from mas.libs.phanpy.plotting.composable.glyphs.area import (
    Rectangle,
    RectangleGlyphStyles,
)
from mas.libs.phanpy.plotting.composable.plot import Plot
from mas.libs.phanpy.plotting.constants import m_internal
from mas.libs.phanpy.plotting.field import (
    StrictDataSpec,
    get_field_props,
    interpret_data_spec,
)
from mas.libs.phanpy.plotting.layer.plot import FacetFilter, PlotConstructorProps
from mas.libs.phanpy.plotting.traits import FillStyleableTrait, LineStyleableTrait
from mas.libs.phanpy.types.primitive import IntegerCollection, NumberLike, ScalarLike
from mas.libs.phanpy.types.typeddict import keysafe_typeddict

HistogramType = Literal["count", "probability", "density"]
BarMode = Literal["stack", "overlay"]


@dataclass
class HistogramHoverTemplateParams:
    x1: pl.Expr
    x2: pl.Expr
    y: pl.Expr


class HistogramHoverTemplate(Protocol):
    def __call__(self, params: HistogramHoverTemplateParams) -> pl.Expr: ...


def default_histogram_hover_template(params: HistogramHoverTemplateParams) -> pl.Expr:
    return pl.format("x = {} - {}<br> y = {}", params.x1, params.x2, params.y)


class HistogramSpec(TypedDict):
    x: StrictDataSpec[NumberLike]
    bins: NotRequired[int | IntegerCollection | Literal["auto"]]
    type: NotRequired[HistogramType]
    mode: NotRequired[BarMode]

    hover_template: NotRequired[HistogramHoverTemplate]

    hover_template: NotRequired[HistogramHoverTemplate]


class HistogramConstructorProps(
    HistogramSpec,
    RectangleGlyphStyles,
    PlotConstructorProps,
):
    pass


class Histogram(
    Plot,
    LineStyleableTrait[RectangleGlyphStyles],
    FillStyleableTrait[RectangleGlyphStyles],
):
    Styles = RectangleGlyphStyles

    def __init__(
        self,
        **props: Unpack[HistogramConstructorProps],
    ) -> None:
        super().__init__(
            **{
                "y_ax": {
                    "typ": "numeric",
                    "range": (0, "auto"),
                },
                **keysafe_typeddict(props, PlotConstructorProps),
            }
        )
        self._spec = keysafe_typeddict(props, HistogramSpec)
        self._styles = keysafe_typeddict(props, RectangleGlyphStyles) or self.Styles()

    def __call__(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: FacetFilter | None,
    ) -> None:
        data, (x_name,) = interpret_data_spec(
            data=self._data,
            x=self._spec["x"],
        )
        bins = self._spec.pop("bins", "auto")
        if not isinstance(bins, ScalarLike):
            bins = np.asarray(bins)
        hist_type = self._spec.pop("type", "count")
        mode = self._spec.pop("mode", "stack")
        density = False
        if hist_type == "density":
            density = True
        styles_d: dict[str, Any] = {**self._styles}
        field_props = get_field_props(styles_d)

        left_name = m_internal("mas.histogram.left")
        right_name = m_internal("mas.histogram.right")
        top_name = m_internal("mas.histogram.top")
        bottom_name = m_internal("mas.histogram.bottom")
        hover_name = m_internal("mas.histogram.hover_text")

        # 如果有 field，那么需要叠
        if len(field_props) > 0:
            field_names = {c.column_name for c in field_props.values()}

            group_name = ",".join(field_names)
            schema: dict[str, PolarsDataType] = {
                **{name: data[name].dtype for name in field_names},
                left_name: pl.List(pl.Float64),
                right_name: pl.List(pl.Float64),
                top_name: pl.List(pl.Float64),
                bottom_name: pl.List(pl.Float64),
            }
            if group_name not in field_names:
                schema[group_name] = pl.String
            merged_df = pl.DataFrame(schema=schema)

            # 先计算一遍 bins
            _, edges = np.histogram(
                data[x_name].drop_nans(), bins=bins, density=density
            )
            bins_nums = len(edges) - 1
            top_values = np.zeros(bins_nums)
            bottom_values = np.zeros(bins_nums)
            for key, group_df in data.group_by(field_names, maintain_order=True):
                group_data = group_df[x_name].drop_nans()
                hist, edges = np.histogram(group_data, bins=edges, density=density)
                if hist_type == "probability":
                    hist = hist / group_data.len()

                if mode == "stack":
                    bottom_values = top_values
                    top_values = hist + top_values
                else:
                    top_values = hist

                to_merge: dict[str, Any] = {
                    left_name: edges[:-1],
                    right_name: edges[1:],
                    top_name: top_values,
                    bottom_name: bottom_values,
                }

                group_v = ",".join([str(o) for o in key])
                if group_name not in field_names:
                    to_merge[group_name] = group_v

                merged_df.vstack(
                    pl.DataFrame(
                        {
                            **{name: value for name, value in zip(field_names, key)},
                            **to_merge,
                        },
                        schema=merged_df.schema,
                    ),
                    in_place=True,
                )
            merged_df = merged_df.explode(
                [left_name, right_name, top_name, bottom_name]
            )

            hover_template = self._spec.pop(
                "hover_template", default_histogram_hover_template
            )
            hover_tooltip = hover_template(
                HistogramHoverTemplateParams(
                    x1=pl.col(left_name), x2=pl.col(right_name), y=pl.col(top_name)
                )
            )

            merged_df = merged_df.with_columns(hover_tooltip.alias(hover_name))

            # 筛选掉 高度为 0 的 矩形数
            merged_df = merged_df.filter(pl.col(top_name) != pl.col(bottom_name))

            (
                Rectangle(
                    left=pl.col(left_name),
                    right=pl.col(right_name),
                    top=pl.col(top_name),
                    bottom=pl.col(bottom_name),
                    name=group_name,
                    legend_group=group_name,
                    **{
                        "fill_alpha": 0.6,
                        **self._styles,
                    },
                )
                .with_hover_tooltip(pl.col(hover_name))
                ._draw(
                    figure=figure,
                    legend=legend,
                    data=data,
                    facet_filter=None,
                )
            )

        else:
            hist, edges = np.histogram(
                data[x_name].drop_nans().drop_nulls(), bins=bins, density=density
            )
            if hist_type == "probability":
                hist = hist / data.height
            data = pl.DataFrame(
                {
                    left_name: edges[:-1],
                    right_name: edges[1:],
                    top_name: hist,
                    bottom_name: np.zeros(hist.shape),
                }
            )
            hover_template = self._spec.pop(
                "hover_template", default_histogram_hover_template
            )
            hover_tooltip = hover_template(
                HistogramHoverTemplateParams(
                    x1=pl.col(left_name), x2=pl.col(right_name), y=pl.col(top_name)
                )
            )
            data = data.with_columns(hover_tooltip.alias(hover_name))

            (
                Rectangle(
                    left=pl.col(left_name),
                    right=pl.col(right_name),
                    top=pl.col(top_name),
                    bottom=pl.col(bottom_name),
                    name=x_name,
                    legend_label=x_name,
                    **{
                        "fill_alpha": 0.6,
                        **self._styles,
                    },
                )
                .with_hover_tooltip(pl.col(hover_name))
                ._draw(
                    figure=figure,
                    legend=legend,
                    data=data,
                    facet_filter=None,
                )
            )

        super().__call__(
            figure=figure,
            legend=legend,
            data=data,
            facet_filter=facet_filter,
        )

    def with_hover_template(self, hover_callable: HistogramHoverTemplate) -> Self:
        self_ = self.copy()
        self_._spec["hover_template"] = hover_callable
        return self_
