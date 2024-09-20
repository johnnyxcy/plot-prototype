# _*_ coding: utf-8 _*_
############################################################
# File: @mas/phanpy\plotting\palette.py
#
# Author: 许翀轶 <chongyi.xu@drugchina.net>
#
# File Created: 08/07/2024 11:28 am
#
# Last Modified: 09/06/2024 01:03 pm
#
# Modified By: 许翀轶 <chongyi.xu@drugchina.net>
#
# Copyright (c) 2024 Maspectra Dev Team
############################################################
from functools import partial
from typing import Callable, Literal, Sequence, cast

import numpy as np
from bokeh.palettes import (
    cividis,
    diverging_palette,
    gray,
    grey,
    inferno,
    interp_palette,
    magma,
    plasma,
    turbo,
    viridis,
)

from mas.libs.phanpy.colors.ggsci import AAAS, JAMA, JCO, NEJM, NPG, Lancet
from mas.libs.phanpy.types.color import ColorLike, HexPalette, Palette

__all__ = [
    "cividis",
    "gray",
    "grey",
    "inferno",
    "magma",
    "plasma",
    "turbo",
    "viridis",
    "diverging_palette",
    "NamedPaletteType",
    "palette_mp",
    "simple_palette",
]


NamedPaletteType = Literal[
    # ggsci
    "NPG",
    "JAMA",
    "NEJM",
    "Lancet",
    "AAAS",
    "JCO",
    # mpl
    "Magma",
    "Inferno",
    "Plasma",
    "Viridis",
    "Cividis",
    "Turbo",
    "Grey",
    "Gray",
]


def ggsci_palette(n: int, name: str, palette: HexPalette, interp: bool = True) -> tuple[str, ...]:
    if len(palette) < n:
        if not interp:
            raise ValueError(f"'{name}' palette only supports {len(palette)} number of colors. {n} is given.")
        else:
            palette = interp_palette(palette, n=n)

    return palette[:n]


palette_mp: dict[NamedPaletteType, Callable[[int], tuple[str, ...]]] = {
    "NPG": partial(ggsci_palette, name="NPG", palette=NPG),
    "JAMA": partial(ggsci_palette, name="JAMA", palette=JAMA),
    "NEJM": partial(ggsci_palette, name="NEJM", palette=NEJM),
    "Lancet": partial(ggsci_palette, name="Lancet", palette=Lancet),
    "AAAS": partial(ggsci_palette, name="AAAS", palette=AAAS),
    "JCO": partial(ggsci_palette, name="JCO", palette=JCO),
    "Magma": magma,
    "Inferno": inferno,
    "Plasma": plasma,
    "Viridis": viridis,
    "Cividis": cividis,
    "Turbo": turbo,
    "Grey": grey,
    "Gray": gray,
}


def polarLUV_to_LUV(H: float, L: float, C: float) -> list[float]:
    H = np.pi / 180.0 * H
    L = L
    U = C * np.cos(H)
    V = C * np.sin(H)
    return [L, U, V]


def LUV_to_XYZ(L: float, U: float, V: float) -> list[float]:
    eps = np.finfo(float).eps * 10
    KAPPA = 903.2962962962963
    XN, YN, ZN = 95.047, 100, 108.883
    Y = YN * (np.power((L + 16.0) / 116.0, 3.0) if L > 8.0 else L / KAPPA)
    L = np.fmax(eps, L)
    t = XN + YN + ZN
    x = XN / t
    y = YN / t
    uN, vN = 2.0 * x / (6.0 * y - x + 1.5), 4.5 * y / (6.0 * y - x + 1.5)
    u = U / (13.0 * L) + uN
    v = V / (13.0 * L) + vN
    X = 9.0 * Y * u / (4 * v)
    Z = -X / 3.0 - 5.0 * Y + 3.0 * Y / v
    return [X, Y, Z]


def XYZ_to_RGB(X: float, Y: float, Z: float) -> tuple[int, int, int]:
    gamma = 2.4
    YN = 100
    # xyz to rgb
    a = [
        (3.240479 * X - 1.537150 * Y - 0.498535 * Z) / YN,  # r
        (-0.969256 * X + 1.875992 * Y + 0.041556 * Z) / YN,  # g
        (0.055648 * X - 0.204043 * Y + 1.057311 * Z) / YN,  # b
    ]
    # rgb->srgb
    val: float
    for i, val in enumerate(a):
        if val > 0.00304:
            val = 1.055 * np.power(val, (1.0 / gamma)) - 0.055
        else:
            val = 12.92 * val
        if val < 0:
            val = 0
        elif val > 1:
            val = 1
        a[i] = val
    R, G, B = round(a[0] * 255), round(a[1] * 255), round(a[2] * 255)
    return R, G, B


def clamp(v: int) -> int:
    return max(0, min(v, 255))


def RGB_to_hex(R: int, G: int, B: int) -> str:
    return "#{0:02x}{1:02x}{2:02x}".format(clamp(R), clamp(G), clamp(B))


def simple_palette(n: int, L: float = 65, C: float = 100, H: float = 15) -> Palette:
    colors: list[ColorLike] = []
    for H_ in np.linspace(H, 375, n + 1):
        L_, U, V = polarLUV_to_LUV(H_, L, C)
        X, Y, Z = LUV_to_XYZ(L_, U, V)
        R, G, B = XYZ_to_RGB(X, Y, Z)
        colors.append(RGB_to_hex(R, G, B))
    return tuple(colors[:-1])


def use_palette(
    n: int,
    palette: NamedPaletteType | tuple[NamedPaletteType, NamedPaletteType] | Sequence[ColorLike] | None = None,
) -> Palette:
    palette_: Palette
    if palette is None:
        palette_ = simple_palette(n)
    elif palette in palette_mp.keys():
        palette_ = palette_mp[cast(NamedPaletteType, palette)](n)
    elif isinstance(palette, tuple) and len(palette) == 2:
        _p1, _p2 = palette
        # mix two palette
        if _p1 in palette_mp.keys() and _p2 in palette_mp.keys():
            palette_ = diverging_palette(
                palette_mp[cast(NamedPaletteType, _p1)](n),
                palette_mp[cast(NamedPaletteType, _p2)](n),
                n=n,
            )
        else:
            palette_ = cast(Palette, palette)
    else:
        palette_ = cast(Palette, palette)
    return palette_
