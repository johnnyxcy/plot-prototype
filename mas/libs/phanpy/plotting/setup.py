# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\setup.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/05/2024 04:10 pm
#
# Last Modified: 08/27/2024 08:56 am
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
import os
import pathlib
import tempfile

import bokeh.io
import bokeh.resources

from mas.libs.phanpy.ipython.detect_ipython import is_ipynb
from mas.libs.phanpy.metaclass.singleton import Singleton
from mas.loggings import logger


class _SetupFlag(metaclass=Singleton):
    is_set = False


def _get_bokeh_resource() -> tuple[bokeh.resources.ResourcesMode, pathlib.Path | None]:
    MAS_BOKEH_ROOTDIR = os.environ.get("mas.resource.bokeh_root_dir", None)
    if MAS_BOKEH_ROOTDIR:
        root_dir = pathlib.Path(MAS_BOKEH_ROOTDIR)
        if not root_dir.exists():
            logger.warning(f"Given bokeh resource dir '{root_dir.as_posix()}' does not exists, fallback to inline")
        else:
            return "relative", root_dir

    return "inline", None


def setup_notebook(reset: bool = False) -> None:
    from bokeh.plotting import curdoc

    if not reset and _SetupFlag.is_set:
        return
    curdoc().theme = "caliber"
    _SetupFlag.is_set = True

    mode, root_dir = _get_bokeh_resource()

    MAS_BOKEH_SHOW_BANNER = os.environ.get("mas.resource.bokeh_show_banner", "0")

    bokeh.io.output_notebook(
        bokeh.resources.Resources(mode=mode, root_dir=root_dir),
        hide_banner=MAS_BOKEH_SHOW_BANNER == "0",
    )


def setup_html(reset: bool = False) -> None:
    from bokeh.plotting import curdoc

    if not reset and _SetupFlag.is_set:
        return
    curdoc().theme = "caliber"
    _SetupFlag.is_set = True
    mode, root_dir = _get_bokeh_resource()

    bokeh.io.output_file(
        pathlib.Path(tempfile.gettempdir()) / "plotting.html",
        mode=mode,
        root_dir=root_dir,
    )


def setup(reset: bool = False) -> None:
    if not reset and _SetupFlag.is_set:
        return
    if is_ipynb():
        setup_notebook(reset)
    else:
        setup_html(reset)
