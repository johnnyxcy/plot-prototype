# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\base.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/05/2024 03:12 pm
#
# Last Modified: 09/14/2024 08:44 am
#
# Modified By: 张凯帆 <you@you.you>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
# 由于 Bokeh 修改属性的方式是动态的，所以我们需要在这个文件中将 reportAttributeAccessIssue 关掉
# pyright: reportAttributeAccessIssue=warning
from __future__ import annotations

import abc
import json
import math
from dataclasses import dataclass
from itertools import product
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Literal,
    Sequence,
    TypedDict,
    cast,
    overload,
)

import bokeh.models as bm
import numpy as np
import polars as pl
from polars._typing import FrameInitTypes, IntoExpr
from typing_extensions import NotRequired, Self, TypeVar, Unpack

from mas.libs.phanpy.plotting.constants import (
    GLYPH_FIELD_TOOLTIPS_COLUMN_NAME,
    PLOT_BACKGROUND_FILL_COLOR,
    PLOT_MARGIN,
    PLOT_TITLE_BACKGROUND_FILL_COLOR,
    RENDERER_TAG,
    GlyphTooltipsTag,
)
from mas.libs.phanpy.plotting.legends import merge_legends
from mas.libs.phanpy.plotting.options import plotting_options
from mas.libs.phanpy.plotting.setup import setup, setup_notebook
from mas.libs.phanpy.plotting.spec import (
    AxSpec,
    CategoricalAxSpec,
    GridLineSpec,
    LegendSpec,
    NumericAxSpec,
    TitleSpec,
    XAxisPlaceType,
    YAxisPlaceType,
    make_axis,
    make_grid_lines,
    make_legend,
    make_range,
    make_scale,
    make_title,
)
from mas.libs.phanpy.types.color import Alpha, ColorLike
from mas.libs.phanpy.types.typeddict import keysafe_typeddict
from mas.libs.phanpy.utils.traits import CopyTrait


class BasePlotLayoutSpec(TypedDict):
    width: NotRequired[int]
    height: NotRequired[int]
    min_border: NotRequired[int]

    background_fill_color: NotRequired[ColorLike]
    background_fill_alpha: NotRequired[Alpha]

    margin: NotRequired[int]


class GridPlotLayoutSpec(TypedDict):
    width: NotRequired[int]
    height: NotRequired[int]
    rows: NotRequired[list[float] | float]
    cols: NotRequired[list[float] | float]

    shared_x_axis: NotRequired[bool]
    shared_y_axis: NotRequired[bool]

    margin: NotRequired[int]


class BasePlotSpec(BasePlotLayoutSpec):
    title: NotRequired[TitleSpec]
    secondary_title: NotRequired[TitleSpec]

    x_ax: NotRequired[AxSpec[XAxisPlaceType]]
    x_grid: NotRequired[GridLineSpec]
    y_ax: NotRequired[AxSpec[YAxisPlaceType]]
    y_grid: NotRequired[GridLineSpec]

    legend: NotRequired[LegendSpec]


RenderedT = TypeVar("RenderedT", bound=bm.LayoutDOM, default=bm.Plot)


@dataclass
class PlotRenderedComponents(Generic[RenderedT]):
    figure: RenderedT
    legend: bm.Legend


class BasePlotDisplay(abc.ABC):
    @abc.abstractmethod
    def render(self) -> bm.LayoutDOM: ...

    def _ipython_display_(self) -> None:
        """Display in ipython"""

        if plotting_options.static_in_nb:
            from bokeh.embed import json_item
            from IPython.display import publish_display_data

            publish_display_data(
                {
                    f"application/vnd.bokehjs.mas.v1+json": json.dumps(
                        json_item(self.render())
                    ),
                }
            )
        else:
            self.show()

    def _repr_html_(self) -> str:
        from bokeh.plotting import show

        setup_notebook()

        display = show(self.render())
        if not display:
            return ""

        return display._repr_html_()

    def show(self) -> None:
        from bokeh.plotting import show

        setup()

        show(self.render())


class BasePlotConstructorProps(BasePlotSpec):
    data: NotRequired[pl.DataFrame | FrameInitTypes | bm.ColumnDataSource]
    parent: NotRequired[bm.Plot]


PlotRenderEventType = Literal["on_before_render", "on_after_rendered"]


OnBeforeRenderHook = Callable[[bm.Plot], None]
OnAfterRenderedHook = Callable[[PlotRenderedComponents], None]


class PlotRenderHooks(TypedDict):
    on_before_render: list[OnBeforeRenderHook]
    on_after_rendered: list[OnAfterRenderedHook]


class BasePlot(CopyTrait, BasePlotDisplay, abc.ABC):
    def __init__(self, **props: Unpack[BasePlotConstructorProps]) -> None:
        self._parent = props.pop("parent", None)
        data = props.pop("data", None)
        if data is not None:
            if isinstance(data, bm.ColumnDataSource):
                self._data = pl.DataFrame(data.data)
            else:
                self._data = pl.DataFrame(data)
        else:
            self._data = None

        self._props = keysafe_typeddict(props, BasePlotSpec)
        self._hooks: PlotRenderHooks = {
            "on_before_render": [],
            "on_after_rendered": [],
        }

    def __deepcopy_memo__(self) -> list[int]:
        if self._parent:
            return [id(self._parent)]
        else:
            return []

    def _handle_callbacks_when(
        self, event: PlotRenderEventType, *args: Any, **kwargs: Any
    ) -> None:
        callbacks = self._hooks.get(event, [])
        for cb in callbacks:
            cb(*args, **kwargs)

    def _render_as_components(self) -> PlotRenderedComponents[bm.Plot]:
        if self._parent:
            fig = self._parent.clone()
        else:
            margin = self._props.get("margin", PLOT_MARGIN)
            fig = bm.Plot(
                height_policy="auto",
                width_policy="auto",
                outline_line_color=None,
                margin=(margin, margin, margin, margin),
                align=("center", "center"),
            )

        # region background
        height = self._props.get("height", None)
        if height:
            fig.height = height
            fig.height_policy = "fixed"
        width = self._props.get("width", None)
        if width:
            fig.width = width
            fig.width_policy = "fixed"
        min_border = self._props.get("min_border", 2)
        fig.min_border = min_border
        fig.background_fill_color = self._props.get(
            "background_fill_color", PLOT_BACKGROUND_FILL_COLOR
        )
        # 先画 grid，因为层级最低
        x_grid = make_grid_lines(
            self._props.get("x_grid", GridLineSpec(visible=False)),
        )
        if x_grid is not None:
            x_grid.dimension = 0
            fig.add_layout(x_grid)
        y_grid = make_grid_lines(
            self._props.get("y_grid", GridLineSpec(visible=False)),
        )
        if y_grid is not None:
            y_grid.dimension = 1
            fig.add_layout(y_grid)
        # endregion

        self._handle_callbacks_when("on_before_render", fig)

        # region ax
        x_ax_spec = self._props.get(
            "x_ax", NumericAxSpec[XAxisPlaceType](typ="numeric")
        )
        y_ax_spec = self._props.get(
            "y_ax", NumericAxSpec[YAxisPlaceType](typ="numeric")
        )

        fig.title = None

        x_axis, mirror_x_axis = make_axis(x_ax_spec)
        if x_axis:
            fig.add_layout(x_axis, "below")
        if mirror_x_axis:
            fig.add_layout(mirror_x_axis, "above")

        fig.x_scale = make_scale(x_ax_spec)
        fig.x_range = make_range(x_ax_spec)
        if x_grid is not None:
            # 更新 grid 的轴
            x_grid.axis = x_axis

        y_axis, mirror_y_axis = make_axis(y_ax_spec)
        if y_axis:
            fig.add_layout(y_axis, "left")
        if mirror_y_axis:
            fig.add_layout(mirror_y_axis, "right")

        fig.y_scale = make_scale(y_ax_spec)
        fig.y_range = make_range(y_ax_spec)
        if y_grid is not None:
            y_grid.axis = y_axis
        # endregion

        # region title
        title_spec = self._props.get("title", TitleSpec())
        title_placement = title_spec.get("placement", "above")
        if title_placement is not None and title_spec.get("text", "") != "":
            if title_placement in ["above", "below"]:
                ax = x_axis
            else:
                ax = y_axis
            title = make_title(
                spec=title_spec,
                ax=ax,
                background_fill_color=PLOT_TITLE_BACKGROUND_FILL_COLOR,
            )
            fig.add_layout(
                title,
                title_placement,
            )

        secondary_title_spec = self._props.get("secondary_title", TitleSpec())
        secondary_title_placement = secondary_title_spec.get("placement", None)
        if (
            secondary_title_placement is not None
            and secondary_title_spec.get("text", "") != ""
        ):
            if secondary_title_placement in ["above", "below"]:
                ax = x_axis
            else:
                ax = y_axis

            title = make_title(
                spec=secondary_title_spec,
                ax=ax,
                background_fill_color=PLOT_TITLE_BACKGROUND_FILL_COLOR,
            )

            fig.add_layout(
                title,
                secondary_title_placement,
            )
        # endregion

        legend_renderer = bm.Legend()

        # region REAL RENDER
        # =====================================================
        self._render(fig, legend_renderer)
        # =====================================================
        # endregion

        # region legend
        legend_spec = self._props.get("legend", LegendSpec(placement="center"))
        legend_placement = legend_spec.get("placement", "center")

        legend_ = make_legend(spec=legend_spec, legend=legend_renderer)
        if legend_placement is not None:
            fig.add_layout(legend_renderer, legend_placement)
        # endregion

        # region toolbars
        hover_tool = bm.HoverTool(
            tooltips=f"<div>@{{{GLYPH_FIELD_TOOLTIPS_COLUMN_NAME}}}</div>",
            renderers=fig.select({"tags": GlyphTooltipsTag.FIELD.value}),
            mode="mouse",
            attachment="horizontal",
            visible=False,
        )
        zoom_tool = bm.BoxZoomTool()
        copy_tool = bm.CopyTool()
        reset_tool = bm.ResetTool()
        move_tool = bm.PanTool()
        fig.toolbar = bm.Toolbar(
            logo=None,
            tools=[
                hover_tool,
                zoom_tool,
                copy_tool,
                reset_tool,
                move_tool,
            ],
            active_drag=zoom_tool,
        )
        fig.toolbar_location = "left"

        # endregion
        rendered = PlotRenderedComponents(
            figure=fig,
            legend=legend_,
        )

        self._handle_callbacks_when("on_after_rendered", rendered)
        return rendered

    def render(self) -> bm.Plot:
        return self._render_as_components().figure

    @abc.abstractmethod
    def _render(self, figure: bm.Plot, legend: bm.Legend) -> None:
        pass

    def with_data(
        self, data: pl.DataFrame | FrameInitTypes | bm.ColumnDataSource
    ) -> Self:
        self_ = self.copy()
        if isinstance(data, bm.ColumnDataSource):
            self_._data = pl.DataFrame(data.data)
        else:
            self_._data = pl.DataFrame(data)
        return self_

    def with_title(self, **spec: Unpack[TitleSpec]) -> Self:
        self_ = self.copy()
        title_ = self_._props.get("title")
        if title_ is None:
            self_._props["title"] = spec
        else:
            title_.update(**spec)
        return self_

    def with_secondary_title(self, **spec: Unpack[TitleSpec]) -> Self:
        self_ = self.copy()
        secondary_title_ = self_._props.get("secondary_title")
        if secondary_title_ is None:
            self_._props["secondary_title"] = spec
        else:
            secondary_title_.update(**spec)
        return self_

    def with_legend_layout(self, **spec: Unpack[LegendSpec]) -> Self:
        self_ = self.copy()
        legend_ = self_._props.get("legend")
        if legend_ is None:
            self_._props["legend"] = spec
        else:
            legend_.update(**spec)

        return self_

    @overload
    def with_x_axis(self, **spec: Unpack[NumericAxSpec[XAxisPlaceType]]) -> Self: ...

    @overload
    def with_x_axis(
        self, **spec: Unpack[CategoricalAxSpec[XAxisPlaceType]]
    ) -> Self: ...

    def with_x_axis(self, **spec: Any) -> Self:
        self_ = self.copy()
        ax_ = self_._props.get("x_ax")
        if ax_ is None:
            self_._props["x_ax"] = cast(AxSpec[XAxisPlaceType], spec)
        else:
            ax_.update(**spec)

        return self_

    @overload
    def with_y_axis(self, **spec: Unpack[NumericAxSpec[YAxisPlaceType]]) -> Self: ...

    @overload
    def with_y_axis(
        self, **spec: Unpack[CategoricalAxSpec[YAxisPlaceType]]
    ) -> Self: ...

    def with_y_axis(self, **spec: Any) -> Self:
        self_ = self.copy()
        ax_ = self_._props.get("y_ax")
        if ax_ is None:
            self_._props["y_ax"] = cast(AxSpec[YAxisPlaceType], spec)
        else:
            ax_.update(**spec)
        return self_

    def with_x_grid(self, **spec: Unpack[GridLineSpec]) -> Self:
        self_ = self.copy()
        x_grid = self_._props.get("x_grid", GridLineSpec())
        x_grid.update(**spec)
        self_._props["x_grid"] = x_grid
        return self_

    def with_y_grid(self, **spec: Unpack[GridLineSpec]) -> Self:
        self_ = self.copy()
        y_grid = self_._props.get("y_grid", GridLineSpec())
        y_grid.update(**spec)
        self_._props["y_grid"] = y_grid
        return self_

    def with_layout(self, **spec: Unpack[BasePlotLayoutSpec]) -> Self:
        self_ = self.copy()
        self_._props.update(**spec)
        return self_

    def facet_wrap(
        self,
        by: IntoExpr | Iterable[IntoExpr],
        n_cols: int | None = None,
        subtitle_factory: Callable[[list[str]], TitleSpec] | None = None,
        **props: Unpack[GridPlotLayoutSpec],
    ) -> GridPlot:
        if self._data is None:
            raise ValueError("facet_wrap cannot be done without providing data source")
        df = pl.DataFrame(self._data)
        children: list[BasePlot] = []

        def make_subtitle(grouped: list[str]) -> TitleSpec:
            if subtitle_factory:
                return subtitle_factory(grouped)
            return TitleSpec(text=",".join(grouped))

        for name, sub_data in df.group_by(by, maintain_order=True):
            child_self_ = self.with_data(sub_data)
            children.append(
                child_self_.with_title(**make_subtitle([str(v) for v in name]))
            )

        return GridPlot(
            children=[*children],
            n_cols=n_cols or min(len(children), 3),
            **props,
        )

    def facet_grid(
        self,
        col: str | pl.Expr,
        row: str | pl.Expr,
        col_title_factory: Callable[[str], TitleSpec] | None = None,
        row_title_factory: Callable[[str], TitleSpec] | None = None,
        shared_x_axis: bool = True,
        shared_y_axis: bool = True,
    ) -> GridPlot:
        if self._data is None:
            raise ValueError("facet_grid cannot be done without providing data source")

        lazy = pl.DataFrame(self._data).lazy()
        if isinstance(row, pl.Expr):
            lazy = lazy.with_columns(row)
            row = row.meta.output_name(raise_if_undetermined=True)

        if isinstance(col, pl.Expr):
            lazy = lazy.with_columns(col)
            col = col.meta.output_name(raise_if_undetermined=True)

        df = lazy.collect()

        def make_col_title(label: str) -> TitleSpec:
            if col_title_factory:
                return col_title_factory(label)
            return TitleSpec(text=f"{col}={label}")

        def make_row_title(label: str) -> TitleSpec:
            if row_title_factory:
                return row_title_factory(label)
            return TitleSpec(text=f"{row}={label}")

        row_groups = df[row].unique().sort()
        col_groups = df[col].unique().sort()

        children: list[list[BasePlot | None]] = [
            [None for _ in range(len(col_groups))] for _ in range(len(row_groups))
        ]
        for row_i, row_v in enumerate(row_groups):
            for col_j, col_v in enumerate(col_groups):
                filtered = df.filter(
                    pl.col(row) == pl.lit(row_v),
                    pl.col(col) == pl.lit(col_v),
                )
                # if filtered.is_empty():
                #     children[row_i][col_j] = None
                # else:
                plot = self.with_data(filtered)
                if row_i == 0:  # first row:
                    plot = plot.with_title(
                        **{
                            **make_col_title(str(col_v)),
                            "placement": "above",
                        }
                    )
                else:
                    plot = plot.with_title(placement=None)  # remove title
                if col_j == len(col_groups) - 1:  # last col
                    plot = plot.with_secondary_title(
                        **{
                            **make_row_title(str(row_v)),
                            "placement": "right",
                        }
                    )
                else:
                    plot = plot.with_secondary_title(placement=None)  # remove title
                children[row_i][col_j] = plot
        return GridPlot.layout(
            children=children,
            shared_x_axis=shared_x_axis,
            shared_y_axis=shared_y_axis,
        )


def auto_rows(
    n_els: int, n_rows: int, n_cols: int, height: int, shared_x_axis: bool
) -> list[float]:
    if shared_x_axis:
        if n_els % n_cols == 0:
            x_axis_percent = 20 / height
            rows_percent = [(1 - x_axis_percent) / n_rows] * n_rows
            rows_percent[-1] = x_axis_percent + rows_percent[-1]
        else:
            x_axis_percent = 20 / height
            rows_percent = [(1 - 2 * x_axis_percent) / n_rows] * n_rows
            rows_percent[-1] = x_axis_percent + rows_percent[-1]
            rows_percent[-2] = x_axis_percent + rows_percent[-2]
    else:
        rows_percent = [1 / n_rows] * n_rows

    return rows_percent


def auto_cols(n_cols: int, width: int, shared_y_axis: bool) -> list[float]:
    if shared_y_axis:
        y_axis_percent = 20 / width
        cols_percent = [(1 - y_axis_percent) / n_cols] * n_cols
        cols_percent[0] = y_axis_percent + cols_percent[0]
    else:
        cols_percent = [1 / n_cols] * n_cols

    return cols_percent


class GridPlot(
    BasePlotDisplay,
    CopyTrait,
):
    def __init__(
        self,
        children: list[BasePlot | None],
        n_cols: int,
        **props: Unpack[GridPlotLayoutSpec],
    ) -> None:
        super().__init__()
        self.__children = [c.copy() if c is not None else None for c in children]
        self.__n_cols = n_cols

        self._layout = keysafe_typeddict(props, GridPlotLayoutSpec)

    @classmethod
    def layout(
        cls,
        children: Sequence[Sequence[BasePlot | None]],
        shared_x_axis: bool = True,
        shared_y_axis: bool = True,
        height: int = 600,
        width: int = 600,
    ) -> Self:
        els = [c for r in children for c in r]
        n_cols = len(children[0] if len(children) > 0 else [])
        return cls(
            children=els,
            n_cols=n_cols,
            shared_x_axis=shared_x_axis,
            shared_y_axis=shared_y_axis,
            height=height,
            width=width,
        )

    @property
    def n_cols(self) -> int:
        return self.__n_cols

    @property
    def n_rows(self) -> int:
        n_els = len(self.__children)
        return math.ceil(n_els / self.n_cols)

    def reshape(self, n_cols: int) -> Self:
        self_ = self.copy(deep=False)
        self_.__n_cols = n_cols
        return self_

    def render(self) -> bm.GridPlot:
        children: list[
            tuple[
                bm.Plot,
                int,  # row index
                int,  # col index
                int,  # row span
                int,  # colspan
            ]
        ] = []
        locator: dict[
            tuple[
                int,  # row index
                int,  # col index
            ],
            bm.Plot,
        ] = {}

        redirecting_tools: list[bm.Tool] = []

        ttl = self.n_cols * self.n_rows
        els: list[BasePlot | None] = [*self.__children]
        els.extend([None] * (ttl - len(els)))
        cols_size = [0] * self.n_cols
        rows_size = [0] * self.n_rows

        reshaped = np.reshape(
            np.asarray(els, dtype=object),
            (self.n_rows, self.n_cols),
        )
        legends: list[bm.Legend] = []
        for row_index, row in enumerate(reshaped):
            el: BasePlot | None
            for col_index, el in enumerate(row):
                if el is not None:
                    legend_placement = el._props.get("legend", {}).get(
                        "placement", "left"
                    )
                    rendered = el.with_legend_layout(
                        placement=None
                    )._render_as_components()
                    if legend_placement is not None:
                        legends.append(rendered.legend)
                    figure = rendered.figure
                    figure.toolbar_location = None
                    children.append((figure, row_index, col_index, 1, 1))
                    locator[(row_index, col_index)] = figure
                    if figure.width:
                        cols_size[col_index] = max(figure.width, cols_size[col_index])
                    if figure.height:
                        rows_size[row_index] = max(figure.height, rows_size[row_index])
                    for tool in figure.tools:
                        if isinstance(tool, bm.ToolProxy):
                            redirecting_tools.extend([*tool.tools])  # type: ignore
                        else:
                            redirecting_tools.append(tool)

        cols = self._layout.get("cols", None)
        rows = self._layout.get("rows", None)
        height = self._layout.get("height", 600)
        width = self._layout.get("width", 600)
        margin = self._layout.get("margin", PLOT_MARGIN)
        is_shared_x_axis = self._layout.get("shared_x_axis", False)
        is_shared_y_axis = self._layout.get("shared_y_axis", False)
        # fix height/width
        if rows is None:
            rows_percent = auto_rows(
                len(children),
                self.n_rows,
                self.n_cols,
                height=height,
                shared_x_axis=is_shared_x_axis,
            )
        elif isinstance(rows, float):
            if rows > 1 or rows < 0:
                raise ValueError("GridPlot rows must be belong (0, 1)")
            rows_percent = [rows] * self.n_rows
        elif isinstance(rows, list):
            if len(rows) != self.n_rows:
                raise ValueError(
                    "rows length must be equal the number of rows in gird plot"
                )
            rows_percent = rows
        else:
            raise ValueError("rows type error")

        if cols is None:
            cols_percent = auto_cols(
                self.n_cols, width=width, shared_y_axis=is_shared_y_axis
            )
        elif isinstance(cols, float):
            if cols > 1 or cols < 0:
                raise ValueError("GridPlot cols must be belong (0, 1)")
            cols_percent = [cols] * self.n_cols
        elif isinstance(cols, list):
            if len(cols) != self.n_cols:
                raise ValueError(
                    "cols length must be equal the number of cols in gird plot"
                )
            cols_percent = cols
        else:
            raise ValueError("cols type error")

        for row_i, col_j in product(range(self.n_rows), range(self.n_cols)):
            fig = locator.get((row_i, col_j), None)
            if fig is None:
                continue
            # height = rows_size[row_i] or 300
            fig.margin = margin
            fig.height = int(height * rows_percent[row_i]) - 2 * margin
            # width = cols_size[col_j] or 200
            fig.width = int(width * cols_percent[col_j]) - 2 * margin

        # 整理共享轴
        # TODO: 现在 x/y 轴在 grid 中的显示是写死的
        # 应该能够支持自由配置
        share_: bm.Plot | None = None
        shared_x_axis: bm.Axis | None = None
        shared_y_axis: bm.Axis | None = None
        if len(children) > 0:
            share_ = children[0][0]
            share_below = [*share_.below]  # type: ignore
            if len(share_below) == 1:
                shared_x_axis = share_below[0].clone()
            share_left = [*share_.left]  # type: ignore
            if len(share_left) == 1:
                shared_y_axis = share_left[0].clone()
            if is_shared_x_axis:
                for col_index in range(self.n_cols):
                    # 最后一行非空的元素是 anchor
                    is_anchor: bool = True
                    # 移除这一列中其余图形的下方的 x 轴，并共享 range/scale
                    for ii in range(self.n_rows - 1, -1, -1):
                        fig = locator.get((ii, col_index), None)
                        if fig is None:
                            continue
                        else:
                            fig.x_range = share_.x_range
                            fig.x_scale = share_.x_scale
                            if is_anchor:
                                is_anchor = False
                                # 移除 x 轴的字
                                for r in fig.below:  # type: ignore
                                    if isinstance(r, bm.Axis):
                                        r.axis_label = None
                            else:
                                # 移除 x 轴 tick 和 tick_label
                                for r in fig.below:  # type: ignore
                                    if isinstance(r, bm.Axis):
                                        r.axis_label = None
                                        r.minor_tick_line_color = None
                                        r.major_tick_line_color = None
                                        r.major_label_text_font_size = "0px"

                                # fig.below = [
                                #     *filter(
                                #         lambda r: not isinstance(r, bm.Axis),
                                #         fig.below,  # type: ignore
                                #     )
                                # ]

            if is_shared_y_axis:
                for row_index in range(self.n_rows):
                    # 第一列非空的元素是 anchor
                    is_anchor: bool = True

                    # 移除这一行中其余图形的左侧的 y 轴，并共享 range/scale
                    for jj in range(self.n_cols):
                        fig = locator.get((row_index, jj), None)
                        if fig is None:
                            continue
                        else:
                            fig.y_range = share_.y_range
                            fig.y_scale = share_.y_scale
                            if is_anchor:
                                is_anchor = False
                                # 移除 y 轴的字
                                for r in fig.left:  # type: ignore
                                    if isinstance(r, bm.Axis):
                                        r.axis_label = None
                            else:
                                for r in fig.left:  # type: ignore
                                    if isinstance(r, bm.Axis):
                                        r.axis_label = None
                                        r.minor_tick_line_color = None
                                        r.major_tick_line_color = None
                                        r.major_label_text_font_size = "0px"
                                # fig.left = [
                                #     *filter(
                                #         lambda r: not isinstance(r, bm.Axis),
                                #         fig.left,  # type: ignore
                                #     )
                                # ]
        # TODO: 设置 width 和 height rows cols 为比例时，无法通过 margin 设置子图间距
        inner_grid = grid = bm.GridPlot(
            children=children,
            toolbar=bm.Toolbar(logo=None, tools=[bm.CopyTool()]),
            styles={"background_color": "#ffffff"},
            width=width + 30,
            height=height,
        )

        if share_:
            axis_grid_children: list[tuple[bm.Plot, int, int]] = []
            # 补充 x/y 轴的内容
            if is_shared_x_axis and shared_x_axis is not None:
                x_axis_plot = bm.Plot(
                    background_fill_color="#ffffff",
                    outline_line_width=0,
                    outline_line_color="#ffffff",
                    min_border=0,
                    margin=0,
                    height_policy="min",
                    width=grid.width,
                    toolbar_location=None,
                    toolbar=bm.Toolbar(logo=None, tools=[bm.CopyTool()]),
                )

                x_axis_label_styles = {}
                for k, v in shared_x_axis.properties_with_values().items():
                    if isinstance(k, str) and k.startswith("axis_label"):
                        x_axis_label_styles[k] = v
                x_axis_plot.add_layout(
                    type(shared_x_axis)(
                        major_tick_line_color=None,
                        minor_tick_line_color=None,
                        axis_line_color=None,
                        axis_label_standoff=0,
                        major_label_text_font_size="0pt",
                    ).clone(**x_axis_label_styles),
                    "below",
                )
                dummy = x_axis_plot.add_glyph(
                    bm.ColumnDataSource(dict(_x=[0], _y=[0])), bm.Line(x="_x", y="_y")
                )
                dummy.visible = False
                axis_grid_children.append((x_axis_plot, 1, 1))
            if is_shared_y_axis and shared_y_axis is not None:
                y_axis_plot = bm.Plot(
                    background_fill_color="#ffffff",
                    outline_line_width=0,
                    outline_line_color="#ffffff",
                    min_border=0,
                    min_width=None,
                    margin=0,
                    width_policy="min",
                    height=grid.height,
                    toolbar_location=None,
                    toolbar=bm.Toolbar(logo=None, tools=[bm.CopyTool()]),
                )

                y_axis_label_styles = {}
                for k, v in shared_y_axis.properties_with_values().items():
                    if isinstance(k, str) and k.startswith("axis_label"):
                        y_axis_label_styles[k] = v
                y_axis_plot.add_layout(
                    type(shared_y_axis)(
                        major_tick_line_color=None,
                        minor_tick_line_color=None,
                        axis_line_color=None,
                        axis_label_standoff=0,
                        major_label_text_font_size="0pt",
                    ).clone(**y_axis_label_styles),
                    "left",
                )
                dummy = y_axis_plot.add_glyph(
                    bm.ColumnDataSource(dict(_x=[0], _y=[0])), bm.Line(x="_x", y="_y")
                )
                dummy.visible = False
                axis_grid_children.append((y_axis_plot, 0, 0))

            if len(axis_grid_children) > 0:
                grid.toolbar_location = None
                grid = bm.GridPlot(
                    children=[
                        *axis_grid_children,
                        (grid, 0, 1),
                    ],
                    toolbar=bm.Toolbar(logo=None, tools=[bm.CopyTool()]),
                    spacing=0,
                    styles={"background_color": "#ffffff"},
                )

        if len(legends) > 0:
            legend_display_plot = bm.Plot(
                renderers=[*inner_grid.select({"tags": RENDERER_TAG})],
                background_fill_color="#ffffff",
                outline_line_width=0,
                outline_line_color="#ffffff",
                toolbar_location=None,
                min_border=0,
                width_policy="min",
            )

            legend_model = legends[0].clone(items=[])
            legend_model = merge_legends(legend_model, *legends)
            if len(legend_model.items) > 0:  # type: ignore
                legend_display_plot.add_layout(legend_model, "left")
                grid.toolbar_location = None
                grid = bm.GridPlot(
                    children=[(grid, 0, 0), (legend_display_plot, 0, 1)],
                    spacing=0,
                    styles={"background_color": "#ffffff"},
                    toolbar=bm.Toolbar(logo=None, tools=[bm.CopyTool()]),
                )

        merged_tools: dict[type[bm.Tool], bm.ToolProxy] = {}
        for tool in redirecting_tools:
            if type(tool) in merged_tools.keys():
                merged_tools[type(tool)].tools.append(tool)
            else:
                merged_tools[type(tool)] = bm.ToolProxy(tools=[tool])

        # Copy 非常 tricky，每个图的复制应该配置给每个图自己，但是 grid 的复制应该是所有子图
        merged_tools.pop(bm.CopyTool, None)
        grid.toolbar.tools = [*merged_tools.values(), bm.CopyTool()]
        grid.toolbar_location = "left"
        grid.toolbar.active_drag = merged_tools.get(bm.BoxZoomTool, None)
        return grid

    def with_layout(self, **spec: Unpack[GridPlotLayoutSpec]) -> GridPlot:
        self_ = self.copy()
        self_._layout.update(**spec)
        return self_
