# 由于 Bokeh 修改属性的方式是动态的，所以我们需要在这个文件中将 reportAttributeAccessIssue 关掉
# pyright: reportAttributeAccessIssue=warning
from __future__ import annotations

import math
from itertools import product
from typing import (
    Sequence,
    TypedDict,
)

import bokeh.models as bm
import numpy as np
from typing_extensions import NotRequired, Self, Unpack

from mas.libs.phanpy.plotting.constants import (
    PLOT_MARGIN,
    RENDERER_TAG,
)
from mas.libs.phanpy.plotting.display import PlotDisplay
from mas.libs.phanpy.plotting.layer.renderable import (
    PlotRenderedComponents,
    RenderableTrait,
)
from mas.libs.phanpy.plotting.legends import merge_legends
from mas.libs.phanpy.types.typeddict import keysafe_typeddict
from mas.libs.phanpy.utils.traits import CopyTrait


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


class GridPlotLayoutSpec(TypedDict):
    width: NotRequired[int]
    height: NotRequired[int]
    rows: NotRequired[list[float] | float]
    cols: NotRequired[list[float] | float]

    shared_x_axis: NotRequired[bool]
    shared_y_axis: NotRequired[bool]

    margin: NotRequired[int]


class GridPlot(
    PlotDisplay,
    CopyTrait,
):
    def __init__(
        self,
        children: list[RenderableTrait | None],
        n_cols: int,
        **props: Unpack[GridPlotLayoutSpec],
    ) -> None:
        super().__init__()
        self.__children: list[RenderableTrait | None] = [
            c if c is not None else None for c in children
        ]
        self.__n_cols = n_cols

        self._layout = keysafe_typeddict(props, GridPlotLayoutSpec)

    @property
    def children(self) -> list[RenderableTrait | None]:
        return self.__children

    def with_layout(self, **spec: Unpack[GridPlotLayoutSpec]) -> GridPlot:
        self_ = self.copy()
        self_._layout.update(**spec)
        return self_

    @classmethod
    def layout(
        cls,
        children: Sequence[Sequence[RenderableTrait | None]],
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

    def _render(self) -> PlotRenderedComponents:
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
        els: list[RenderableTrait | None] = [*self.__children]
        els.extend([None] * (ttl - len(els)))
        cols_size = [0] * self.n_cols
        rows_size = [0] * self.n_rows

        reshaped = np.reshape(
            np.asarray(els, dtype=object),
            (self.n_rows, self.n_cols),
        )
        legends: list[bm.Legend] = []
        for row_index, row in enumerate(reshaped):
            el: RenderableTrait | None
            for col_index, el in enumerate(row):
                if el is not None:
                    # legend_placement = el._props.get("legend", {}).get(
                    #     "placement", "left"
                    # )
                    rendered = el._render()
                    if rendered.legend is not None:
                        legends.append(rendered.legend)
                    figure = rendered.figure

                    if isinstance(figure, bm.Plot):
                        children.append((figure, row_index, col_index, 1, 1))
                        locator[(row_index, col_index)] = figure
                        figure.toolbar_location = None
                        if figure.width:
                            cols_size[col_index] = max(
                                figure.width, cols_size[col_index]
                            )
                        if figure.height:
                            rows_size[row_index] = max(
                                figure.height, rows_size[row_index]
                            )
                        for tool in figure.tools:
                            if isinstance(tool, bm.ToolProxy):
                                redirecting_tools.extend([*tool.tools])  # type: ignore
                            else:
                                redirecting_tools.append(tool)
                    else:
                        raise NotImplementedError(
                            "Nested gridplot is not implemented yet"
                        )

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
        else:
            legend_model = None
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
        return PlotRenderedComponents(figure=grid, legend=legend_model)
