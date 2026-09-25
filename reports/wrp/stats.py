"""Weighted estimates used throughout the report scripts.

Conventions (see reports/README.md):

- Weight: PROJWT by default. PROJWT is WGT scaled up to each country's
  adult population, so it is proportional to WGT within every country:
  country figures are identical under either weight, and global or
  regional figures are population-weighted, as in the reports.
- Base: rows where the variable is missing (question not asked) are always
  dropped. Don't know / refused answers stay in the base unless listed in
  `exclude`, which is how Gallup reports percentages by default.
"""

import pandas as pd

DEFAULT_WEIGHT = "PROJWT"


def _grouped(df, by):
    if by is None:
        return [((), df)]
    return df.groupby(by, observed=True, sort=True)


def _series(results, by):
    if by is None:
        return results[()]
    index = pd.MultiIndex.from_tuples(results) if isinstance(by, list) and len(by) > 1 else list(results)
    return pd.Series(list(results.values()), index=index, dtype=float)


def wmean(df, value, weight=DEFAULT_WEIGHT, by=None):
    """Weighted mean of `value` over rows where it is present.

    Returns a float, or a Series indexed by the `by` groups.
    """
    results = {}
    for key, g in _grouped(df, by):
        g = g[g[value].notna()]
        results[key] = (g[value] * g[weight]).sum() / g[weight].sum() if len(g) else float("nan")
    return _series(results, by)


def pct(df, var, codes, weight=DEFAULT_WEIGHT, by=None, exclude=None):
    """Weighted % of respondents whose `var` is one of `codes`.

    exclude: codes dropped from the base, e.g. [98, 99] to report among
    those giving a substantive answer. Default keeps DK/refused in the base.
    """
    codes = list(codes) if isinstance(codes, (list, tuple, set, range)) else [codes]
    exclude = list(exclude or [])
    results = {}
    for key, g in _grouped(df, by):
        g = g[g[var].notna() & ~g[var].isin(exclude)]
        w = g[weight]
        results[key] = 100 * w[g[var].isin(codes)].sum() / w.sum() if len(g) else float("nan")
    return _series(results, by)


def distribution(df, var, weight=DEFAULT_WEIGHT, by=None, exclude=None, labels=None):
    """Weighted % in every answer category of `var` (rows sum to 100).

    labels: optional code -> label dict (see wrp.value_labels) used to name
    the columns.
    """
    exclude = list(exclude or [])
    d = df[df[var].notna() & ~df[var].isin(exclude)]
    keys = by if by is not None else (lambda _: "All")
    table = d.pivot_table(index=keys, columns=var, values=weight, aggfunc="sum", fill_value=0)
    table = 100 * table.div(table.sum(axis=1), axis=0)
    if labels:
        table = table.rename(columns=labels)
    return table.iloc[0] if by is None else table
