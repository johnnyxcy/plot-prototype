from __future__ import annotations

import abc
from dataclasses import dataclass

import bokeh.models as bm


@dataclass
class PlotRenderedComponents:
    figure: bm.LayoutDOM
    legend: bm.Legend | None = None


class RenderableTrait(abc.ABC):
    @abc.abstractmethod
    def _render(self) -> PlotRenderedComponents:
        pass

    def render(self) -> bm.LayoutDOM:
        return self._render().figure
