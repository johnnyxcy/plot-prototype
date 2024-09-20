# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\options.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 09/12/2024 08:10 am
#
# Last Modified: 09/12/2024 08:42 am
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
import typing

from pydantic import BaseModel, Field

__all__ = ["PlottingOptions", "plotting_options"]


@typing.final
class PlottingOptions(BaseModel):
    """Options for modeling and simulation"""

    static_in_nb: bool = Field(default=False)


plotting_options: typing.Final[PlottingOptions] = PlottingOptions()
