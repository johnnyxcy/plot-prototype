# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\legends.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 04:32 pm
#
# Last Modified: 08/16/2024 10:20 am
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
# pyright: reportAttributeAccessIssue=warning
import bokeh.models as bm
import numpy as np
from bokeh.core.properties import field, value
from bokeh.core.property.vectorization import Field, Value


def _find_legend_item(label: Field | Value, legend: bm.Legend) -> bm.LegendItem | None:
    for item in legend.items:  # type: ignore
        if item.label == label:
            return item
    return None


def handle_legend_field(
    label: str,
    legend: bm.Legend,
    glyph_renderer: bm.GlyphRenderer,
) -> None:
    if not isinstance(label, str):
        raise ValueError("legend_field value must be a string")
    label_ = field(label)
    item = _find_legend_item(label_, legend)
    if item:
        item.renderers.append(glyph_renderer)
    else:
        item = bm.LegendItem(label=label_, renderers=[glyph_renderer])
        legend.items.append(item)


def handle_legend_group(
    label: str,
    legend: bm.Legend,
    glyph_renderer: bm.GlyphRenderer,
) -> None:
    if not isinstance(label, str):
        raise ValueError("legend_group value must be a string")

    source = glyph_renderer.data_source
    if source is None:
        raise ValueError(
            "Cannot use 'legend_group' on a glyph without a data source already configured"
        )
    if not (hasattr(source, "column_names") and label in source.column_names):
        raise ValueError("Column to be grouped does not exist in glyph data source")

    column = np.asarray(source.data[label])
    # 如果类型是 Series[list]，需要做 concatenate，所以这里处理
    if len(column) > 0 and isinstance(column[0], list | np.ndarray):
        column = np.concatenate(column)

    vals, inds = np.unique(column, return_index=True)

    for val, ind in zip(vals, inds):
        label_ = value(f"{label}={str(val)}")
        item = _find_legend_item(label_, legend)
        if item:
            item.renderers.append(glyph_renderer)
        else:
            item = bm.LegendItem(label=label_, renderers=[glyph_renderer], index=ind)
            legend.items.append(item)


def handle_legend_label(
    label: str,
    legend: bm.Legend,
    glyph_renderer: bm.GlyphRenderer,
):
    if not isinstance(label, str):
        raise ValueError("legend_label value must be a string")
    label_ = value(label)
    item = _find_legend_item(label_, legend)
    if item:
        item.renderers.append(glyph_renderer)
    else:
        item = bm.LegendItem(label=label_, renderers=[glyph_renderer])
        legend.items.append(item)


def merge_legend_item_renderers(
    a: bm.LegendItem, renderers: list[bm.GlyphRenderer]
) -> list[bm.GlyphRenderer]:
    merged: list[bm.GlyphRenderer] = [*a.renderers]  # type: ignore
    for r in renderers:
        if not r.visible:
            continue
        renderers_to_merge: list[bm.GlyphRenderer] = []
        a_r: bm.GlyphRenderer
        for a_r in merged:  # type: ignore
            if (a_r.glyph.id == r.glyph.id) or (a_r.glyph.name == r.glyph.name):
                continue
            else:
                renderers_to_merge.append(a_r)
        merged.extend(renderers_to_merge)

    return merged


def merge_legends(a: bm.Legend, *b: bm.Legend) -> bm.Legend:
    merged = a.clone()
    items_to_merge: list[bm.LegendItem] = []
    for legend_to_merge in b:
        items_to_merge.extend(legend_to_merge.items)  # pyright: ignore[reportArgumentType]

    for item in items_to_merge:
        found_item = _find_legend_item(item.label, merged)  # pyright: ignore[reportArgumentType]
        if found_item:
            found_item.renderers = merge_legend_item_renderers(
                found_item,
                item.renderers,  # pyright: ignore[reportArgumentType]
            )
        else:
            merged.items.append(item)
    return merged
