# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\constants.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 03:12 pm
#
# Last Modified: 09/12/2024 10:51 am
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
import enum
from typing import Final


def m_internal(s: str) -> str:
    return "__{s}__".format(s=s)


def is_internal(s: str) -> bool:
    return s.startswith("__") and s.endswith("__")


RENDERER_TAG: Final = m_internal("mas.plotting.renderer")


GLYPH_FIELD_TOOLTIPS_TAG: Final = m_internal("mas.plotting.glyph.tooltips.field")
GLYPH_FIELD_TOOLTIPS_COLUMN_NAME: Final = GLYPH_FIELD_TOOLTIPS_TAG
GLYPH_FILED_VISIBLE_COLUMN_NAME: Final = m_internal("mas.plotting.glyph.column.visible")


@enum.unique
class GlyphTooltipsTag(enum.Enum):
    FIELD = GLYPH_FIELD_TOOLTIPS_TAG


PLOT_MARGIN = 8
PLOT_BACKGROUND_FILL_COLOR = "#ffffff"
PLOT_TITLE_BACKGROUND_FILL_COLOR = "#cecece"
