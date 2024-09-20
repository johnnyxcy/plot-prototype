# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\props.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/06/2024 01:58 pm
#
# Last Modified: 09/09/2024 10:28 am
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from typing import TypedDict

from bokeh.core.enums import (
    FontStyleType,
    JitterRandomDistributionType,
    LineCapType,
    LineDashType,
    LineJoinType,
    MarkerTypeType,
    TextAlignType,
    TextBaselineType,
)
from typing_extensions import NotRequired

from mas.libs.phanpy.plotting.field import FieldSpecConstructor
from mas.libs.phanpy.types.color import Alpha, ColorLike


class BaseTextProps(TypedDict):
    text_alpha: NotRequired[Alpha]
    text_font: NotRequired[str]
    text_font_size: NotRequired[str]
    text_font_style: NotRequired[FontStyleType]
    text_align: NotRequired[TextAlignType]
    text_baseline: NotRequired[TextBaselineType]
    text_line_height: NotRequired[float]


class ScalarTextProps(BaseTextProps):
    text_color: NotRequired[ColorLike]


class TextProps(BaseTextProps):
    text_color: NotRequired[ColorLike | None | FieldSpecConstructor[ColorLike]]


class BaseLineProps(TypedDict):
    line_alpha: NotRequired[Alpha]  # 0-1
    line_width: NotRequired[float]
    line_join: NotRequired[LineJoinType]
    line_cap: NotRequired[LineCapType]
    line_dash_offset: NotRequired[int]


class ScalarLineProps(BaseLineProps):
    line_color: NotRequired[ColorLike | None]
    line_dash: NotRequired[LineDashType]


class LineProps(BaseLineProps):
    line_color: NotRequired[ColorLike | None | FieldSpecConstructor[ColorLike]]
    line_dash: NotRequired[LineDashType | FieldSpecConstructor[LineDashType]]


class BaseFillProps(TypedDict):
    fill_alpha: NotRequired[Alpha]


class ScalarFillProps(BaseFillProps):
    fill_color: NotRequired[ColorLike | None]


class FillProps(BaseFillProps):
    fill_color: NotRequired[ColorLike | None | FieldSpecConstructor[ColorLike]]


class MarkerProps(TypedDict):
    marker: NotRequired[MarkerTypeType | FieldSpecConstructor[MarkerTypeType]]
    size: NotRequired[float | FieldSpecConstructor[float]]
    angle: NotRequired[float]


class JitterProps(TypedDict):
    width: NotRequired[float]
    mean: NotRequired[float]
    distribution: NotRequired[JitterRandomDistributionType]
