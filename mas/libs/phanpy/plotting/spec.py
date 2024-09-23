# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\spec.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/08/2024 03:11 pm
#
# Last Modified: 09/13/2024 05:19 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from __future__ import annotations

from typing import Any, Generic, Iterable, Literal, cast

import bokeh.models as bm
import polars as pl
from bokeh.core.enums import (
    AlignType,
    FontStyleType,
    LabelOrientationType,
    LegendLocationType,
    LineCapType,
    LineDashType,
    LineJoinType,
    OrientationType,
    PlaceType,
    TextAlignType,
    TextBaselineType,
)
from polars._typing import IntoExpr
from typing_extensions import (  # 必须要从 typing_extension 里面导入，否则不支持继承 Generic
    NotRequired,
    TypedDict,
    TypeVar,
    Unpack,
)

from mas.libs.phanpy.plotting.layer.grid import GridPlotLayoutSpec
from mas.libs.phanpy.plotting.props import ScalarTextProps
from mas.libs.phanpy.types.color import Alpha, ColorLike
from mas.libs.phanpy.types.primitive import TextLikeCollection
from mas.libs.phanpy.types.typeddict import keysafe_typeddict

XAxisPlaceType = Literal["above", "below"]
YAxisPlaceType = Literal["left", "right"]
AxisPlaceType = XAxisPlaceType | YAxisPlaceType

AxisPlaceTypeT = TypeVar("AxisPlaceTypeT", XAxisPlaceType, YAxisPlaceType)


class RawAxSpec(TypedDict):
    axis_label: NotRequired[str]
    axis_label_standoff: NotRequired[int]
    axis_label_orientation: NotRequired[LabelOrientationType]
    axis_label_align: NotRequired[AlignType]
    axis_label_text_color: NotRequired[ColorLike]
    axis_label_text_alpha: NotRequired[Alpha]
    axis_label_text_font: NotRequired[str]
    axis_label_text_font_size: NotRequired[str]
    axis_label_text_font_style: NotRequired[FontStyleType]
    axis_label_text_align: NotRequired[TextAlignType]
    axis_label_text_baseline: NotRequired[TextBaselineType]
    axis_label_text_line_height: NotRequired[float]

    background_fill_color: NotRequired[ColorLike]
    background_fill_alpha: NotRequired[Alpha]

    minor_tick_line_color: NotRequired[ColorLike | None]
    major_tick_line_color: NotRequired[ColorLike | None]
    major_label_text_font_size: NotRequired[str]


class CommonAxSpec(
    RawAxSpec,
    Generic[AxisPlaceTypeT],
):
    # placement: NotRequired[AxisPlaceTypeT | None]
    # placement: NotRequired[AxisPlaceTypeT | None]
    visible: NotRequired[bool]
    mirror: NotRequired[RawAxSpec | bool]


NumericRangeSpec = (
    tuple[
        float | Literal["auto"] | None,
        float | Literal["auto"] | None,
    ]
    | Literal["auto"]
)


class NumericAxSpec(CommonAxSpec[AxisPlaceTypeT]):
    typ: NotRequired[Literal["numeric"]]
    scale: NotRequired[Literal["linear", "log"]]
    range: NotRequired[NumericRangeSpec]

    # ticker
    num_minor_ticks: NotRequired[int]
    desired_num_ticks: NotRequired[int]


class CategoricalAxSpec(CommonAxSpec[AxisPlaceTypeT]):
    typ: Literal["categorical"]
    factors: TextLikeCollection


AxSpec = NumericAxSpec[AxisPlaceTypeT] | CategoricalAxSpec[AxisPlaceTypeT]


def make_axis(spec: AxSpec[AxisPlaceTypeT]) -> tuple[bm.Axis | None, bm.Axis | None]:
    visible = spec.get("visible", True)
    if visible:
        mirror = spec.get("mirror", True)
    else:
        mirror = spec.get("mirror", False)

    if visible or mirror:
        typ = spec.get("typ", "numeric")
        if typ == "numeric":
            spec = cast(NumericAxSpec[AxisPlaceTypeT], spec)
            scale = spec.get("scale", "linear")
            desired_num_ticks = spec.get("desired_num_ticks", 6)
            num_minor_ticks = spec.get("num_minor_ticks", 5)
            if scale == "linear":
                axis = bm.LinearAxis(
                    ticker=bm.BasicTicker(
                        desired_num_ticks=desired_num_ticks,
                        num_minor_ticks=num_minor_ticks,
                    )
                )
            elif scale == "log":
                axis = bm.LogAxis(
                    ticker=bm.LogTicker(
                        desired_num_ticks=desired_num_ticks,
                        num_minor_ticks=num_minor_ticks,
                    )
                )
            else:
                raise TypeError()
        elif typ == "categorical":
            spec = cast(CategoricalAxSpec[AxisPlaceTypeT], spec)
            axis = bm.CategoricalAxis()
        else:
            raise TypeError()
        mirror_axis = axis.clone()
        if visible:
            axis.update(
                **keysafe_typeddict(
                    spec,
                    RawAxSpec,
                    axis_label_standoff=0,
                )
            )
        else:
            axis = None

        if isinstance(mirror, bool) and mirror:  # == True
            # 默认不显示 tick 和 tick_label
            mirror_axis_prop = {}
            mirror_axis_prop.setdefault("major_label_text_font_size", "0px")
            mirror_axis_prop.setdefault("major_tick_line_color", None)
            mirror_axis_prop.setdefault("minor_tick_line_color", None)
            mirror_axis.update(**mirror_axis_prop)
        elif mirror:  # RawAxSpec
            mirror_axis.update(**mirror)
        else:
            mirror_axis = None

        return axis, mirror_axis

    return None, None


def make_scale(spec: AxSpec[AxisPlaceTypeT]) -> bm.Scale:
    typ = spec.get("typ", "numeric")
    if typ == "numeric":
        scale = spec.get("scale", "linear")
        if scale == "linear":
            return bm.LinearScale()

        if scale == "log":
            return bm.LogScale()
    elif typ == "categorical":
        return bm.CategoricalScale()

    raise TypeError()


class TitleSpec(ScalarTextProps):
    text: NotRequired[str]
    placement: NotRequired[AxisPlaceType | None]

    background_fill_color: NotRequired[ColorLike]
    background_fill_alpha: NotRequired[Alpha]


def make_title(
    spec: TitleSpec,
    ax: AxSpec[Any] | bm.Axis | None,
    **defaults: Unpack[TitleSpec],
) -> bm.Axis:
    spec = {**defaults, **spec.copy()}

    text = spec.pop("text", "")
    if isinstance(ax, bm.Axis):
        axis_cls = type(ax)
    elif ax is None:
        axis_cls = bm.LinearAxis
    else:
        axis, mirror = make_axis(ax)
        axis = axis or mirror
        if axis:
            axis_cls = type(axis)
        else:
            axis_cls = bm.LinearAxis

    title_axis = axis_cls(
        axis_label=text,
        major_tick_line_color=None,
        minor_tick_line_color=None,
        axis_line_color=None,
        axis_label_standoff=0,
        major_label_text_font_size="0pt",
    )

    text_props = keysafe_typeddict(spec, ScalarTextProps)
    text_props_with_prefix = {}
    for k, v in text_props.items():
        text_props_with_prefix[f"axis_label_{k}"] = v
    title_axis.update(**text_props_with_prefix)

    background_fill_color = spec.get("background_fill_color", None)
    if background_fill_color:
        title_axis.background_fill_color = background_fill_color  # pyright: ignore[reportAttributeAccessIssue]
    background_fill_alpha = spec.get("background_fill_alpha", None)
    if background_fill_alpha:
        title_axis.background_fill_alpha = background_fill_alpha  # pyright: ignore[reportAttributeAccessIssue]

    return title_axis


def make_range(ax: AxSpec[Any]) -> bm.Range:
    typ = ax.get("typ", "numeric")
    if typ == "numeric":
        range_: NumericRangeSpec = ax.get("range", "auto")
        if range_ == "auto":
            return bm.DataRange1d()

        start, end = range_

        if start != "auto" and end != "auto":
            return bm.Range1d(start=start, end=end)
        else:
            range_m = bm.DataRange1d()
            if start != "auto":
                range_m.start = start  # pyright: ignore[reportAttributeAccessIssue]
            if end != "auto":
                range_m.end = end  # pyright: ignore[reportAttributeAccessIssue]

            return range_m
    else:
        factors_: TextLikeCollection | None = ax.get("factors", None)
        if factors_ is None:
            raise ValueError(
                "You must provide factors if no data is provided with categorical axis"
            )

        return bm.FactorRange(factors=list(factors_))


class MajorGridLineProps(TypedDict):
    grid_line_color: NotRequired[ColorLike]
    grid_line_alpha: NotRequired[Alpha]  # 0-1
    grid_line_width: NotRequired[float]
    grid_line_join: NotRequired[LineJoinType]
    grid_line_cap: NotRequired[LineCapType]
    grid_line_dash: NotRequired[LineDashType]
    grid_line_dash_offset: NotRequired[int]


class MinorGridLineProps(TypedDict):
    minor_grid_line_color: NotRequired[ColorLike]
    minor_grid_line_alpha: NotRequired[Alpha]  # 0-1
    minor_grid_line_width: NotRequired[float]
    minor_grid_line_join: NotRequired[LineJoinType]
    minor_grid_line_cap: NotRequired[LineCapType]
    minor_grid_line_dash: NotRequired[LineDashType]
    minor_grid_line_dash_offset: NotRequired[int]


class GridLineSpec(
    MajorGridLineProps,
    MinorGridLineProps,
):
    visible: NotRequired[bool]
    minor_visible: NotRequired[bool]


def make_grid_lines(
    spec: GridLineSpec, **defaults: Unpack[GridLineSpec]
) -> bm.Grid | None:
    grid = bm.Grid(**defaults)
    visible = spec.get("visible", True)
    if visible:
        grid_props = keysafe_typeddict(spec, MajorGridLineProps)
        grid.update(**grid_props)
    else:
        return None

    minor_visible = spec.get("minor_visible", True)
    if minor_visible:
        minor_grid_props = keysafe_typeddict(
            spec,
            MinorGridLineProps,
        )
        grid.update(**minor_grid_props)
    else:
        grid.minor_grid_line_color = None  # pyright: ignore[reportAttributeAccessIssue]

    return grid


class LegendSpec(TypedDict):
    placement: NotRequired[PlaceType | None]
    location: NotRequired[LegendLocationType]
    orientation: NotRequired[OrientationType]
    n_cols: NotRequired[int]
    n_rows: NotRequired[int]

    title: NotRequired[str]
    title_text_color: NotRequired[ColorLike]
    title_text_alpha: NotRequired[Alpha]
    title_text_font: NotRequired[str]
    title_text_font_size: NotRequired[str]
    title_text_font_style: NotRequired[FontStyleType]
    title_text_align: NotRequired[TextAlignType]
    title_text_baseline: NotRequired[TextBaselineType]
    title_text_line_height: NotRequired[float]

    label_text_color: NotRequired[ColorLike]
    label_text_alpha: NotRequired[Alpha]
    label_text_font: NotRequired[str]
    label_text_font_size: NotRequired[str]
    label_text_font_style: NotRequired[FontStyleType]
    label_text_align: NotRequired[TextAlignType]
    label_text_baseline: NotRequired[TextBaselineType]
    label_text_line_height: NotRequired[float]

    background_fill_color: NotRequired[ColorLike]
    background_fill_alpha: NotRequired[Alpha]


def make_legend(spec: LegendSpec, legend: bm.Legend | None = None) -> bm.Legend:
    spec_ = {**spec.copy()}
    spec_.pop("placement", None)
    if legend is None:
        legend = bm.Legend()
    n_cols = spec_.pop("n_cols", None)
    if n_cols is not None:
        spec_["ncols"] = n_cols
    n_rows = spec_.pop("n_rows", None)
    if n_rows is not None:
        spec_["nrows"] = n_rows
    legend.update(**spec_)

    return legend


class BaseFacetSpec(GridPlotLayoutSpec):
    pass


class FacetWrapSpec(BaseFacetSpec):
    style: Literal["wrap"]
    by: IntoExpr | Iterable[IntoExpr]
    n_cols: int | None


class FacetGridSpec(BaseFacetSpec):
    style: Literal["grid"]
    colname: str | pl.Expr
    rowname: str | pl.Expr


FacetSpec = FacetWrapSpec | FacetGridSpec
