# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\stats\boxplot.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/08/2024 10:13 am
#
# Last Modified: 09/12/2024 02:56 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from dataclasses import dataclass
from typing import Any, Protocol, TypedDict

import bokeh.models as bm
import numpy as np
import polars as pl
from typing_extensions import NotRequired, Self, Unpack

from mas.libs.phanpy.plotting.base import BasePlotConstructorProps
from mas.libs.phanpy.plotting.composable.glyphs.abstract import GlyphRenderable
from mas.libs.phanpy.plotting.composable.glyphs.bar import BarGlyphStyles
from mas.libs.phanpy.plotting.composable.plot import Plot
from mas.libs.phanpy.plotting.constants import m_internal
from mas.libs.phanpy.plotting.field import (
    DataSpec,
    field_,
    get_field_props,
    interpret_data_spec,
    replace_field_props,
)
from mas.libs.phanpy.plotting.props import FillProps, LineProps
from mas.libs.phanpy.plotting.render import render_glyph
from mas.libs.phanpy.plotting.traits import FillStyleableTrait, LineStyleableTrait
from mas.libs.phanpy.types.primitive import Percentile
from mas.libs.phanpy.types.typeddict import keysafe_typeddict


@dataclass
class BoxPlotHoverTemplateParams:
    cat: pl.Expr
    min: pl.Expr
    q1: pl.Expr
    q2: pl.Expr
    q3: pl.Expr
    max: pl.Expr


class BoxPlotHoverTemplate(Protocol):
    def __call__(self, params: BoxPlotHoverTemplateParams) -> pl.Expr: ...


def default_box_plot_hover_template(params: BoxPlotHoverTemplateParams) -> pl.Expr:
    return pl.format(
        "{}<br>Min = {}<br>Q1 = {}<br>Median = {}<br>Q3 = {}<br>Max = {}",
        params.cat,
        params.min,
        params.q1,
        params.q2,
        params.q3,
        params.max,
    )


class BoxPlotSpec(TypedDict):
    x: DataSpec
    y: DataSpec

    q_lower: NotRequired[Percentile]
    q_middle: NotRequired[Percentile]
    q_upper: NotRequired[Percentile]
    q_outlier: NotRequired[float]

    hover_template: NotRequired[BoxPlotHoverTemplate]


class RawBoxPlotConstructorProps(
    BarGlyphStyles,
    BasePlotConstructorProps,
):
    pass


class BoxPlotConstructorProps(BoxPlotSpec, RawBoxPlotConstructorProps):
    pass


class BoxPlot(
    Plot,
    FillStyleableTrait[BarGlyphStyles],
    LineStyleableTrait[BarGlyphStyles],
):
    Styles = BarGlyphStyles

    def __init__(
        self,
        **props: Unpack[BoxPlotConstructorProps],
    ) -> None:
        super().__init__(**props)
        self._spec = keysafe_typeddict(props, BoxPlotSpec)
        self._styles = keysafe_typeddict(props, BarGlyphStyles) or BoxPlot.Styles()

    def _render(self, figure: bm.Plot, legend: bm.Legend) -> None:
        data, (x_name, y_name) = interpret_data_spec(
            data=self._data,
            x=self._spec["x"],
            y=self._spec["y"],
        )

        styles_d: dict[str, Any] = {"fill_alpha": 1, **self._styles}
        field_props = get_field_props(styles_d)

        if data[x_name].dtype.is_numeric() and not data[y_name].dtype.is_numeric():
            # 对 x 进行统计
            stats_on_name = x_name
            cat_on_name = y_name
            dimension = "width"
        elif not data[x_name].dtype.is_numeric() and data[y_name].dtype.is_numeric():
            # 对 y 进行统计
            stats_on_name = y_name
            cat_on_name = x_name
            dimension = "height"
        else:
            raise ValueError("x/y must be a numeric/categorical pair")

        q1_name = m_internal("mas.boxplot.q1")
        q2_name = m_internal("mas.boxplot.q2")
        q3_name = m_internal("mas.boxplot.q3")
        iqr_name = m_internal("mas.boxplot.iqr")
        qmin_name = m_internal("mas.boxplot.lower")
        qmax_name = m_internal("mas.boxplot.upper")

        # 如果有 field，那么分组计算统计量
        if len(field_props) > 0:
            by = {c.column_name for c in field_props.values()}
        else:
            by = []

        range_min = data[stats_on_name].nan_min()
        range_max = data[stats_on_name].nan_max()

        group_columns = set([cat_on_name, *by])
        group_name = ",".join(set(group_columns))

        q1_level = self._spec.get("q_lower", 0.25)
        q2_level = self._spec.get("q_middle", 0.5)
        q3_level = self._spec.get("q_upper", 0.75)
        q_outlier_level = self._spec.get("q_outlier", 1.5)

        stats_data = (
            data.lazy()
            .group_by(*group_columns)
            .agg(
                pl.col(stats_on_name),
                pl.col(stats_on_name).quantile(q1_level).alias(q1_name),
                pl.col(stats_on_name).quantile(q2_level).alias(q2_name),
                pl.col(stats_on_name).quantile(q3_level).alias(q3_name),
            )
            .with_columns(
                (pl.col(q3_name) - pl.col(q1_name)).alias(iqr_name),
            )
            .with_columns(
                (pl.col(q3_name) + q_outlier_level * pl.col(iqr_name)).alias(qmax_name),
                (pl.col(q3_name) - q_outlier_level * pl.col(iqr_name)).alias(qmin_name),
            )
        )
        if group_name not in stats_data.collect_schema().names():
            stats_data = stats_data.with_columns(
                pl.concat_str(
                    [pl.col(label) for label in group_columns],
                    separator=",",
                ).alias(group_name)
            )
        stats_data = stats_data.collect()

        range_max = max(range_max, stats_data[qmax_name].nan_max())
        range_min = min(range_min, stats_data[qmin_name].nan_min())
        assert isinstance(range_max, int | float)
        assert isinstance(range_min, int | float)
        range_max = range_max * 1.1
        range_min = range_min * 0.9

        (styles_d, stats_data) = replace_field_props(styles_d, data=stats_data)

        hover_template = self._spec.pop("hover_template", None)
        if hover_template:
            tooltip_template = hover_template(
                BoxPlotHoverTemplateParams(
                    cat=pl.col(cat_on_name),
                    min=pl.col(qmin_name),
                    q1=pl.col(q1_name),
                    q2=pl.col(q2_name),
                    q3=pl.col(q3_name),
                    max=pl.col(qmax_name),
                )
            )
        else:
            tooltip_template = pl.concat_str(
                pl.lit("<b>"),
                pl.col(group_name),
                pl.lit("</b>"),
                pl.lit("<br>"),
                pl.format("q(min)={}", pl.col(qmin_name)),
                pl.lit("<br>"),
                pl.format(f"q({q1_level})={{}}", pl.col(q1_name)),
                pl.lit("<br>"),
                pl.format(f"q({q2_level})={{}}", pl.col(q2_name)),
                pl.lit("<br>"),
                pl.format(f"q({q3_level})={{}}", pl.col(q3_name)),
                pl.lit("<br>"),
                pl.format("q(max)={}", pl.col(qmax_name)),
            )

        for _, grouped_df in stats_data.group_by(cat_on_name):
            if len(by) > 0:
                grouped_df = grouped_df.sort(*by)
            n_subgroups = grouped_df.height
            size = 0.5 / n_subgroups
            if n_subgroups == 1:
                dodge_values = [0.0]
            else:
                dodge_values = np.linspace(-0.25, 0.25, n_subgroups)

            for idx, dodge_value in enumerate(dodge_values):
                df_i = grouped_df[idx]
                if dimension == "height":
                    range_ = figure.x_range
                else:
                    range_ = figure.y_range
                cat_variable = field_(
                    cat_on_name,
                    bm.Dodge(
                        value=dodge_value,
                        range=range_,
                    ),
                )
                # 先画 whisker, 因为图层在最下面
                figure.add_layout(
                    bm.Whisker(
                        base=cat_variable,
                        upper=q1_name,
                        lower=qmin_name,
                        dimension=dimension,
                        level="underlay",
                        lower_head=bm.TeeHead(
                            **keysafe_typeddict(styles_d, LineProps), size=10
                        ),
                        upper_head=bm.TeeHead(line_width=0),
                        source=bm.ColumnDataSource(df_i.to_dict()),
                        **keysafe_typeddict(styles_d, LineProps),
                    )
                )
                figure.add_layout(
                    bm.Whisker(
                        base=cat_variable,
                        upper=qmax_name,
                        lower=q3_name,
                        dimension=dimension,
                        level="underlay",
                        lower_head=bm.TeeHead(line_width=0),
                        upper_head=bm.TeeHead(
                            **keysafe_typeddict(styles_d, LineProps), size=10
                        ),
                        source=bm.ColumnDataSource(df_i.to_dict()),
                        **keysafe_typeddict(styles_d, LineProps),
                    )
                )

                outliers = df_i.explode(stats_on_name).filter(
                    pl.col(stats_on_name)
                    .is_between(
                        pl.col(qmin_name),
                        pl.col(qmax_name),
                    )
                    .not_()
                )

                if dimension == "height":
                    render_glyph(
                        data=df_i,
                        glyph=bm.VBar(
                            x=cat_variable,
                            top=q3_name,
                            bottom=q1_name,
                            width=size,
                            **styles_d,
                        ),
                        figure=figure,
                        legend=legend,
                        legend_spec={
                            "legend_type": "group",
                            "legend_value": group_name,
                        },
                        tooltip_template=tooltip_template,
                    )
                    render_glyph(
                        data=df_i,
                        glyph=bm.VBar(
                            x=cat_variable,
                            top=q2_name,
                            bottom=q2_name,
                            width=size,
                            **styles_d,
                        ),
                        figure=figure,
                    )

                    if outliers.height > 0:
                        # TODO: 需要将 scatter 样式接口暴露给外层
                        scatter_fill_style = keysafe_typeddict(styles_d, FillProps)
                        scatter_fill_style["fill_alpha"] = 0
                        render_glyph(
                            name="outlier",
                            data=outliers,
                            glyph=bm.Scatter(
                                x=cat_variable,
                                y=stats_on_name,
                                **keysafe_typeddict(styles_d, LineProps),
                                **scatter_fill_style,
                            ),
                            figure=figure,
                            tooltip_template=pl.format(
                                f"{stats_on_name}={{}}",
                                pl.col(stats_on_name),
                            ),
                        )
                else:
                    render_glyph(
                        data=df_i,
                        glyph=bm.HBar(
                            y=cat_variable,
                            left=q3_name,
                            right=q1_name,
                            height=size,
                            **styles_d,
                        ),
                        figure=figure,
                        legend=legend,
                        legend_spec={
                            "legend_type": "group",
                            "legend_value": group_name,
                        },
                        tooltip_template=tooltip_template,
                    )
                    render_glyph(
                        data=df_i,
                        glyph=bm.HBar(
                            y=cat_variable,
                            left=q2_name,
                            right=q2_name,
                            height=size,
                            **styles_d,
                        ),
                        figure=figure,
                    )
                    if outliers.height > 0:
                        render_glyph(
                            name="outlier",
                            data=outliers,
                            glyph=bm.Scatter(
                                x=stats_on_name,
                                y=cat_variable,
                                **keysafe_typeddict(styles_d, LineProps),
                                **keysafe_typeddict(styles_d, FillProps),
                            ),
                            figure=figure,
                            tooltip_template=pl.format(
                                f"{stats_on_name}={{}}",
                                pl.col(stats_on_name),
                            ),
                        )

        if dimension == "height":
            # TODO: 考虑应该将图的 collect 阶段和 render 阶段分开
            y_ax = self._props.get("y_ax", None)
            if y_ax is None or y_ax.get("range", None) is None:
                figure.y_range = bm.Range1d(range_min, range_max)  # pyright: ignore[reportAttributeAccessIssue]
            #     self._props["y_ax"] = {
            #         "typ": "numeric",
            #         "range": (range_min, range_max),
            #     }
        else:
            x_ax = self._props.get("x_ax", None)
            if x_ax is None or x_ax.get("range", None) is None:
                figure.x_range = bm.Range1d(range_min, range_max)  # pyright: ignore[reportAttributeAccessIssue]
            # # 更新 axis 默认值
            # x_ax = self._props.get("x_ax", None)
            # if x_ax is None:
            #     self._props["x_ax"] = {
            #         "typ": "numeric",
            #         "range": (range_min, range_max),
            #     }
            # y_ax = self._props.get("y_ax", None)
            # if y_ax is None:
            #     self._props["y_ax"] = {
            #         "typ": "categorical",
            #         "factors": df[cat_on_name].unique().sort().to_list(),
            #     }
        self._do_render(
            GlyphRenderable(
                figure=figure,
                legend=legend,
                data=data,
            )
        )

    def with_hover_template(self, hover_callable: BoxPlotHoverTemplate) -> Self:
        self_ = self.copy()
        self_._spec["hover_template"] = hover_callable
        return self_
