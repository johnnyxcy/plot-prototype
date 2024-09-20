# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\composable\stats\trend.py
#
# Author: 姚泽 <ze.yao@drugchina.net>
#
# File Created: 09/11/2024 01:37 pm
#
# Last Modified: 09/11/2024 01:38 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################

import numpy as np
import numpy.typing as npt
import polars as pl

from mas.libs.phanpy.plotting.composable.glyphs.line import Segment


def trend_line(data: pl.DataFrame, x: str, y: str) -> Segment:
    data = data.filter(
        pl.col(x).is_null().or_(pl.col(x).is_nan()).or_(pl.col(y).is_null().or_(pl.col(y).is_nan())).not_()
    )
    x_data: npt.NDArray[np.float_] = data[x].to_numpy()
    y_data: npt.NDArray[np.float_] = data[y].to_numpy()
    k, b = np.polyfit(x_data, y_data, deg=1)

    x1 = x_data.min()
    y1 = k * x1 + b
    x2 = x_data.max()
    y2 = k * x2 + b

    return Segment(x0=x1, y0=y1, x1=x2, y1=y2)
