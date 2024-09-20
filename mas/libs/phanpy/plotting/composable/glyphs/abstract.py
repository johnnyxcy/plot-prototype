# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\glyphs\abstract.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 05:52 pm
#
# Last Modified: 08/30/2024 02:12 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
import abc
from typing import Any, Literal, overload

import bokeh.models as bm
import polars as pl
from bokeh.core.enums import RenderLevelType
from typing_extensions import Self

from mas.libs.phanpy.plotting.composable.renderable import GlyphRenderable
from mas.libs.phanpy.plotting.field import (
    FieldSpecConstructorCls,
    get_field_props,
    handle_spec_constructor,
)
from mas.libs.phanpy.plotting.render import (
    GlyphLegendSpec,
    render_glyph,
    typesafe_glyph_legend,
)
from mas.libs.phanpy.utils.traits import CopyTrait


class GlyphSpec(CopyTrait, abc.ABC):
    def __init__(
        self,
        name: str | None = None,
        legend: GlyphLegendSpec | None = None,
        tooltip_template: pl.Expr | Literal[False] | None = None,
    ) -> None:
        self.__name = name
        self.__legend = legend
        self.__tooltip_template: pl.Expr | Literal[False] | None = tooltip_template

    @property
    def name(self) -> str | None:
        return self.__name

    def with_hover_tooltip(
        self,
        __tooltip_template: pl.Expr | Literal[False],
    ) -> Self:
        self_ = self.copy()
        self_.__tooltip_template = __tooltip_template
        return self_

    @overload
    def with_legend(
        self,
        legend_label: str,
    ) -> Self: ...

    @overload
    def with_legend(
        self,
        *,
        legend_group: str,
    ) -> Self: ...

    def with_legend(
        self,
        legend_label: str | None = None,
        *,
        legend_group: str | None = None,
    ) -> Self:
        self_ = self.copy()
        self_.__legend = typesafe_glyph_legend(
            legend_label=legend_label,
            legend_group=legend_group,
        )
        return self_

    def render_glyph(
        self,
        figure: bm.Plot,
        legend: bm.Legend | None,
        data: pl.DataFrame,
        glyph: bm.Glyph,
        level: RenderLevelType = "glyph",
        default_tooltip_template: pl.Expr | None = None,
    ) -> bm.GlyphRenderer:
        if self.__tooltip_template is None:
            # 使用 default
            tooltip_template = default_tooltip_template
        elif self.__tooltip_template is False:
            tooltip_template = None
        else:
            tooltip_template = self.__tooltip_template
        return render_glyph(
            data=data,
            glyph=glyph,
            figure=figure,
            legend=legend,
            name=self.__name,
            legend_spec=self.__legend,
            tooltip_template=tooltip_template,
            level=level,
        )

    def render_glyph_with_reducing_props(
        self,
        figure: bm.Plot,
        legend: bm.Legend | None,
        data: pl.DataFrame,
        glyph: bm.Glyph,
        props: dict[str, Any],
        level: RenderLevelType = "glyph",
        default_tooltip_template: pl.Expr | None = None,
    ) -> None:
        field_props = get_field_props(props)
        if len(field_props) == 0:
            self.render_glyph(
                data=data,
                glyph=glyph.clone(**props),
                figure=figure,
                legend=legend,
                level=level,
                default_tooltip_template=default_tooltip_template,
            )
            return

        field_names = {c.column_name for c in field_props.values()}
        grouped = data.group_by(field_names).agg(pl.all())
        props_to_reduce: dict[str, str] = {}
        for k, v in props.items():
            if isinstance(v, FieldSpecConstructorCls):
                _field_name, grouped = handle_spec_constructor(
                    constructor=v,
                    data=grouped,
                )
                props_to_reduce[k] = _field_name
        for i in range(grouped.height):
            # 一张一张画
            _props = props.copy()
            for prop_key_to_reduce, field_name_to_reduce in props_to_reduce.items():
                _props[prop_key_to_reduce] = grouped[field_name_to_reduce][i]
            glyph = glyph.clone(**_props)
            self.render_glyph(
                data=grouped[i].explode(
                    pl.all().exclude(field_names, *props_to_reduce.values())
                ),
                glyph=glyph,
                figure=figure,
                legend=legend,
                level=level,
                default_tooltip_template=(
                    pl.concat_str(
                        default_tooltip_template,
                        *[
                            pl.concat_str(
                                pl.lit("<br>"),
                                pl.format("{}={}", pl.lit(name), pl.col(name)),
                            )
                            for name in field_names
                        ],
                    )
                    if default_tooltip_template is not None
                    else None
                ),
            )

    @abc.abstractmethod
    def _draw(self, renderable: GlyphRenderable) -> None:
        pass
