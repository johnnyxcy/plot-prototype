# pyright: reportAttributeAccessIssue=none
from __future__ import annotations

from typing import Any, Iterable, Protocol, TypedDict, cast, overload

import bokeh.models as bm
import polars as pl
from polars._typing import FrameInitTypes, IntoExpr
from typing_extensions import NotRequired, Self, Unpack

from mas.libs.phanpy.plotting.constants import (
    GLYPH_FIELD_TOOLTIPS_COLUMN_NAME,
    PLOT_BACKGROUND_FILL_COLOR,
    PLOT_MARGIN,
    GlyphTooltipsTag,
)
from mas.libs.phanpy.plotting.display import PlotDisplay
from mas.libs.phanpy.plotting.layer.grid import GridPlot, GridPlotLayoutSpec
from mas.libs.phanpy.plotting.layer.renderable import (
    PlotRenderedComponents,
    RenderableTrait,
)
from mas.libs.phanpy.plotting.spec import (
    AxSpec,
    CategoricalAxSpec,
    FacetGridSpec,
    FacetSpec,
    FacetWrapSpec,
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
)
from mas.libs.phanpy.types.color import Alpha, ColorLike
from mas.libs.phanpy.types.typeddict import keysafe_typeddict
from mas.libs.phanpy.utils.traits import CopyTrait


class PlotLayoutSpec(TypedDict):
    width: NotRequired[int]
    height: NotRequired[int]
    min_border: NotRequired[int]

    background_fill_color: NotRequired[ColorLike]
    background_fill_alpha: NotRequired[Alpha]

    margin: NotRequired[int]


class PlotSpec(PlotLayoutSpec):
    title: NotRequired[TitleSpec]
    secondary_title: NotRequired[TitleSpec]

    x_ax: NotRequired[AxSpec[XAxisPlaceType]]
    x_grid: NotRequired[GridLineSpec]
    y_ax: NotRequired[AxSpec[YAxisPlaceType]]
    y_grid: NotRequired[GridLineSpec]

    legend: NotRequired[LegendSpec]


class PlotConstructorProps(PlotSpec):
    data: NotRequired[pl.DataFrame | FrameInitTypes | bm.ColumnDataSource]
    facet: NotRequired[FacetSpec]


class DrawFuncType(Protocol):
    def __call__(
        self,
        figure: bm.Plot,
        legend: bm.Legend,
        data: pl.DataFrame | None,
        facet_filter: pl.Expr | None,
    ) -> None: ...


class PlotDrawer(RenderableTrait):
    def __init__(
        self,
        on_draw: DrawFuncType,
        data: pl.DataFrame | None,
        facet_filter: pl.Expr | None,
        props: PlotSpec,
    ) -> None:
        self._on_draw = on_draw
        self._data = data
        self._props = props
        self._facet_filter = facet_filter

    def _render(
        self,
    ) -> PlotRenderedComponents:
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

        legend_renderer = bm.Legend()

        # region REAL RENDER
        # =====================================================
        self._on_draw(
            figure=fig,
            legend=legend_renderer,
            data=self._data,
            facet_filter=self._facet_filter,
        )
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
        return rendered


class Plot(
    CopyTrait,
    PlotDisplay,
    DrawFuncType,
):
    def __init__(self, **props: Unpack[PlotConstructorProps]) -> None:
        data = props.pop("data", None)
        if data is not None:
            if isinstance(data, bm.ColumnDataSource):
                self._data = pl.DataFrame(data.data)
            else:
                self._data = pl.DataFrame(data)
        else:
            self._data = None

        facet = props.pop("facet", None)
        self._facet = facet
        self._props = keysafe_typeddict(props, PlotSpec)

    def _as_renderable(
        self,
        filter: pl.Expr | None = None,
    ) -> PlotDrawer:
        def on_draw(
            figure: bm.Plot,
            legend: bm.Legend,
            data: pl.DataFrame | None,
            facet_filter: pl.Expr | None,
        ) -> None:
            self(figure, legend, data, facet_filter)

        return PlotDrawer(
            on_draw=on_draw,
            data=self._data,
            facet_filter=filter,
            props=self._props,
        )

    def _render_facet(self, facet: FacetSpec) -> PlotRenderedComponents:
        if facet["style"] == "wrap":
            return self._render_facet_wrap(facet)
        elif facet["style"] == "grid":
            return self._render_facet_grid(facet)
        else:
            raise ValueError(f"Unknown facet type: {facet}")

    def _render_facet_wrap(
        self,
        facet: FacetWrapSpec,
    ) -> PlotRenderedComponents:
        if self._data is None:
            raise ValueError("facet_wrap cannot be done without providing data source")
        df = self._data
        children: list[RenderableTrait] = []
        by = facet["by"]
        n_cols = facet["n_cols"]
        props = keysafe_typeddict(facet, GridPlotLayoutSpec)

        combs = df.select(by).unique().sort(by)

        for combination in combs.iter_rows(named=True):
            filter_ = pl.lit(True)
            for colname, value in combination.items():
                filter_ = filter_ & (pl.col(colname) == value)
            rendered = self._as_renderable(filter=filter_)
            children.append(rendered)

        return GridPlot(
            children=[*children],
            n_cols=n_cols or min(len(children), 3),
            **props,
        )._render()

    def _render_facet_grid(
        self,
        facet: FacetGridSpec,
    ) -> PlotRenderedComponents:
        raise NotImplementedError()

    def _render(self) -> PlotRenderedComponents:
        facet = self._facet

        if facet is None:
            return self._as_renderable()._render()
        else:
            return self._render_facet(facet)

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

    def with_layout(self, **spec: Unpack[PlotLayoutSpec]) -> Self:
        self_ = self.copy()
        self_._props.update(**spec)
        return self_

    def with_facet_none(self) -> Self:
        self_ = self.copy()
        self_._facet = None
        return self_

    def with_facet_wrap(
        self,
        by: IntoExpr | Iterable[IntoExpr],
        n_cols: int | None = None,
        **props: Unpack[GridPlotLayoutSpec],
    ) -> Self:
        self_ = self.copy()
        self_._facet = FacetWrapSpec(
            style="wrap",
            by=by,
            n_cols=n_cols,
            **props,
        )
        return self_

    def with_facet_grid(
        self,
        colname: str | pl.Expr,
        rowname: str | pl.Expr,
        **props: Unpack[GridPlotLayoutSpec],
    ) -> Self:
        self_ = self.copy()
        self_._facet = FacetGridSpec(
            style="grid",
            colname=colname,
            rowname=rowname,
            **props,
        )
        return self_
