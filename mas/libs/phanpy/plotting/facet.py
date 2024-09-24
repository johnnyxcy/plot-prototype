from typing import Any, Iterable

import polars as pl

FacetFilter = dict[str, Any]


def facet_filter_as_str(
    facet_filter: FacetFilter | None,
    named: bool = False,
) -> str:
    if facet_filter is None:
        return ""
    return "\n".join([f"{k}={v}" if named else str(v) for k, v in facet_filter.items()])


def apply_facet_filter(
    data: pl.DataFrame,
    facet_filter: FacetFilter | None,
) -> pl.DataFrame:
    if facet_filter is not None:
        for k in facet_filter.keys():
            if k not in data.columns:
                return data

        data_ = data.lazy()
        for k, v in facet_filter.items():
            data_ = data_.filter(pl.col(k) == v)
        return data_.collect()
    else:
        return data


def split_facet_filter_for_stats(
    facet_filter: FacetFilter | None,
    stats_groupby: Iterable[str],
) -> tuple[FacetFilter | None, FacetFilter | None]:
    if facet_filter is None:
        return None, None

    stats_filter: FacetFilter = {}
    glyph_filter: FacetFilter = {}
    for k, v in facet_filter.items():
        if k in stats_groupby:
            glyph_filter[k] = v
        else:
            stats_filter[k] = v

    return stats_filter, glyph_filter
