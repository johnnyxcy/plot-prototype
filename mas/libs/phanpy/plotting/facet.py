from typing import Any

import polars as pl

FacetFilter = dict[str, Any]


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
