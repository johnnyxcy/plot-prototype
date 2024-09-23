# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\traits.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 05:51 pm
#
# Last Modified: 08/19/2024 04:57 pm
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from typing import Generic, TypeVar

from typing_extensions import Self, Unpack

from mas.libs.phanpy.plotting.props import FillProps, LineProps, MarkerProps, TextProps
from mas.libs.phanpy.utils.traits import Copyable

LinePropsT = TypeVar("LinePropsT", bound=LineProps)
FillPropsT = TypeVar("FillPropsT", bound=FillProps)
MarkerPropsT = TypeVar("MarkerPropsT", bound=MarkerProps)
TextPropsT = TypeVar("TextPropsT", bound=TextProps)


class LineStyleableTrait(
    Copyable,
    Generic[LinePropsT],
):
    _styles: LinePropsT

    def with_line_styles(self, **styles: Unpack[LineProps]) -> Self:
        self_ = self.copy()
        self_._styles.update(**styles)
        return self_


class FillStyleableTrait(
    Copyable,
    Generic[FillPropsT],
):
    _styles: FillPropsT

    def with_fill_styles(self, **styles: Unpack[FillProps]) -> Self:
        self_ = self.copy()
        self_._styles.update(**styles)
        return self_


class MarkerStylableTrait(
    Copyable,
    Generic[MarkerPropsT],
):
    _styles: MarkerPropsT

    def with_marker_styles(self, **styles: Unpack[MarkerProps]) -> Self:
        self_ = self.copy()
        self_._styles.update(**styles)
        return self_


class TextStyleableTrait(
    Copyable,
    Generic[TextPropsT],
):
    _styles: TextPropsT

    def with_text_styles(self, **styles: Unpack[TextProps]) -> Self:
        self_ = self.copy()
        self_._styles.update(**styles)
        return self_
