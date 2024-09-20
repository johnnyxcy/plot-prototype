# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\field.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/13/2024 03:13 pm
#
# Last Modified: 08/26/2024 01:55 pm
#
# Modified By: 姚泽 <ze.yao@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
import abc
import functools
from dataclasses import dataclass
from typing import Any, Callable, Collection

import polars as pl
from bokeh.core.property.vectorization import Field as BokehField
from polars._typing import IntoExpr, NonNestedLiteral
from typing_extensions import Generic, Protocol, TypeVar

from mas.libs.phanpy.types.primitive import ScalarLike
from mas.loggings import logger

T = TypeVar("T", default=Any)
DataT = TypeVar("DataT", bound=NonNestedLiteral, default=ScalarLike)


@dataclass
class FieldSpec(Generic[T]):
    column_name: str


@dataclass
class TransformFieldSpec(FieldSpec[T]):
    transformed_column_name: str

    @abc.abstractmethod
    def transform_expr(self) -> pl.Expr:
        pass

    @abc.abstractmethod
    def transform(self, data: pl.DataFrame) -> pl.DataFrame:
        pass


@dataclass
class FactorMapTransformFieldSpec(TransformFieldSpec[T]):
    mapper: dict[Any, T]

    def transform_expr(self) -> pl.Expr:
        return (
            pl.col(self.column_name)
            .replace_strict(self.mapper)
            .alias(
                self.transformed_column_name,
            )
        )

    def transform(self, data: pl.DataFrame) -> pl.DataFrame:
        return data.with_columns(self.transform_expr())


@dataclass
class PolarsExprTransformFieldSpec(TransformFieldSpec[T]):
    expr: pl.Expr

    def transform_expr(self) -> pl.Expr:
        return self.expr

    def transform(self, data: pl.DataFrame) -> pl.DataFrame:
        return data.with_columns(self.expr)


class FieldSpecConstructorLike(Protocol[T]):
    def __call__(self, data: pl.DataFrame) -> FieldSpec[T]: ...


class DelegateFieldSpecConstructor(FieldSpecConstructorLike[T]):
    def __init__(
        self,
        column_name: str,
        constructor: FieldSpecConstructorLike[T],
    ) -> None:
        self.column_name = column_name
        self.__constructor = constructor

    def __call__(self, data: pl.DataFrame) -> FieldSpec[T]:
        return self.__constructor(data)


FieldSpecConstructorCls = DelegateFieldSpecConstructor | pl.Expr
FieldSpecConstructor = DelegateFieldSpecConstructor[T] | pl.Expr

StrictDataSpec = FieldSpecConstructor[DataT] | Collection[DataT]
DataSpec = (
    FieldSpecConstructor[DataT] | Collection[DataT] | DataT
)  # Scalar will automatically expanded


class polars_expr_as_field_spec_constructor(Generic[T]):
    def __new__(
        cls,
        constructor: pl.Expr,
    ) -> DelegateFieldSpecConstructor[T]:
        root_names = constructor.meta.root_names()
        column_name = constructor.meta.output_name()

        def _constructor(data: pl.DataFrame) -> FieldSpec[T]:
            for from_name in root_names:
                if from_name not in data.columns:
                    raise KeyError(f"{from_name} not found in column names")
            return PolarsExprTransformFieldSpec(
                column_name=column_name,
                transformed_column_name=column_name,
                expr=constructor,
            )

        return DelegateFieldSpecConstructor(
            # TODO: @xuchongyi 这里是有 bug 的，如果生成列依赖多个输入列，这里没法正确的 groupby，需要额外处理
            column_name=column_name,
            constructor=_constructor,
        )


class typeguard_field_spec_constructor(Generic[T]):
    def __new__(
        cls,
        constructor: FieldSpecConstructor[T],
    ) -> DelegateFieldSpecConstructor[T]:
        if isinstance(constructor, pl.Expr):
            return polars_expr_as_field_spec_constructor(constructor)
        else:
            return constructor


def _ensure_height_matches(name: str, height: int, current: int | None) -> int:
    if current is None:
        return height
    else:
        # check if height does not matches
        if height != current:
            raise pl.exceptions.ShapeError(
                f"Height for data spec mismatched for '{name}'"
            )
        return current


def interpret_data_spec(
    data: pl.DataFrame | None,
    **named_spec: DataSpec[Any],
) -> tuple[pl.DataFrame, tuple[str, ...]]:
    lazy_exprs: list[IntoExpr | Callable[[int], IntoExpr]] = []
    height: int | None = None
    output_names: list[str] = []

    for name, v in named_spec.items():
        if isinstance(v, pl.Expr):
            v = polars_expr_as_field_spec_constructor(v)
        if isinstance(v, DelegateFieldSpecConstructor):
            if data is None:
                raise ValueError(
                    "Data must be provided with expression like data spec."
                )
            spec = v(data)
            height = _ensure_height_matches(name, data.height, height)
            if isinstance(spec, TransformFieldSpec):

                def _(n: int, *, spec: TransformFieldSpec) -> pl.Expr:
                    return spec.transform_expr()

                lazy_exprs.append(functools.partial(_, spec=spec))
                output_name = spec.transformed_column_name
            else:
                if spec.column_name not in data.columns:
                    raise pl.exceptions.ColumnNotFoundError(
                        f"Column '{spec.column_name}' not exists"
                    )
                lazy_exprs.append(data[spec.column_name])
                output_name = spec.column_name
        elif isinstance(v, Collection) and not isinstance(
            v, str
        ):  # !IMPORTANT: 单个字符串是 Collection
            height = _ensure_height_matches(name, len(v), height)
            lazy_exprs.append(pl.Series(name, v))
            output_name = name
        else:  # is scalar

            def _(n: int, *, name: str, value: pl.Expr) -> pl.Expr:
                return pl.repeat(value, n).alias(name)

            lazy_exprs.append(functools.partial(_, name=name, value=pl.lit(v)))
            output_name = name

        if output_name in output_names:
            logger.warning(
                f"{output_name} appears multiple times in data specs. It might cause unexpected behavior"
            )

        output_names.append(output_name)

    if height is None:
        if data is None:
            height = 1
        else:
            height = data.height
    elif data is not None and data.height != height:
        data = pl.DataFrame()

    lazy: pl.LazyFrame
    if data is not None:
        lazy = data.lazy()
    else:
        lazy = pl.DataFrame().lazy()

    for lazy_expr in lazy_exprs:
        if callable(lazy_expr):
            expr_ = lazy_expr(height)
        else:
            expr_ = lazy_expr
        lazy = lazy.with_columns(expr_)

    return lazy.collect(), tuple(output_names)


def get_field_props(d: dict[str, Any]) -> dict[str, DelegateFieldSpecConstructor[Any]]:
    field_props: dict[str, DelegateFieldSpecConstructor[Any]] = {}
    for k, v in d.items():
        if isinstance(v, FieldSpecConstructorCls):
            field_props[k] = typeguard_field_spec_constructor[Any](v)
    return field_props


def handle_spec_constructor(
    constructor: FieldSpecConstructorCls,
    data: pl.DataFrame,
) -> tuple[str, pl.DataFrame]:
    spec_constructor = typeguard_field_spec_constructor(constructor)
    spec = spec_constructor(data)
    if isinstance(spec, TransformFieldSpec):
        data = spec.transform(data)
        column_name = spec.transformed_column_name
    else:
        column_name = spec.column_name

    return column_name, data


DictT = TypeVar("DictT", bound=dict, default=dict[str, Any])

DictKey = str
FieldName = str


@dataclass
class ReplacedFieldProps(Generic[DictT]):
    d: DictT
    replaced_props: dict[DictKey, FieldName]
    data: pl.DataFrame


def field_(field: str, *args: Any, **kwargs: Any) -> BokehField:
    return BokehField(field, *args, **kwargs)


def replace_field_props2(d: DictT, data: pl.DataFrame) -> ReplacedFieldProps[DictT]:
    replaced_props: dict[str, str] = {}
    d = d.copy()
    for k, v in d.items():
        if isinstance(v, FieldSpecConstructorCls):
            field_name, data = handle_spec_constructor(
                constructor=v,
                data=data,
            )
            replaced_props[k] = field_name
            d[k] = field_(field_name)

    return ReplacedFieldProps[DictT](
        d=d,
        data=data,
        replaced_props=replaced_props,
    )


def replace_field_props(
    d: dict[str, Any], data: pl.DataFrame
) -> tuple[dict[str, Any], pl.DataFrame]:
    for k, v in d.items():
        if isinstance(v, FieldSpecConstructorCls):
            field_name, data = handle_spec_constructor(
                constructor=v,
                data=data,
            )
            d[k] = field_(field_name)

    return d, data
