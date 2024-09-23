# # _*_ coding: utf-8 _*_
# ############################################################
# # File: @mas/phanpy\plotting\composable\renderable.py
# #
# # Author: 许翀轶 <chongyi.xu@drugchina.net>
# #
# # File Created: 08/19/2024 08:18 am
# #
# # Last Modified: 08/19/2024 08:20 am
# #
# # Modified By: 许翀轶 <chongyi.xu@drugchina.net>
# #
# # Copyright (c) 2024 Maspectra Dev Team
# ############################################################
# from dataclasses import dataclass, replace
# from typing import Any

# import bokeh.models as bm
# import polars as pl
# from bokeh.core.enums import RenderLevelType
# from typing_extensions import Self

# from mas.libs.phanpy.plotting.layer.plot import FacetSpec


# @dataclass
# class GlyphRenderable:
#     figure: bm.Plot
#     legend: bm.Legend | None
#     data: pl.DataFrame | None
#     level: RenderLevelType = "glyph"

#     facet: FacetSpec | None = None

#     def with_(self, **kwargs: Any) -> Self:
#         return replace(self, **kwargs)
