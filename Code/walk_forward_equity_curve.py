"""Display current-run multi-asset walk-forward equity-style curves."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from plot_config import (
    AGENT_COLORS,
    DEFAULT_FIGSIZE,
    ZERO_LINE_COLOR,
    add_figure_caption,
    apply_axis_number_format,
    apply_clean_style,
    format_agent_name,
    save_chart,
    show_chart,
)

try:
    from strategy_config import AGENT_ORDER
    from timeframe_config import RESEARCH_TIMEFRAME_LABEL
    from walk_forward_plot_utils import (
        load_walk_forward_panel_summary,
        walk_forward_metadata,
        walk_forward_tickers,
    )
except ModuleNotFoundError:
    from Code.strategy_config import AGENT_ORDER
    from Code.timeframe_config import RESEARCH_TIMEFRAME_LABEL
    from Code.walk_forward_plot_utils import (
        load_walk_forward_panel_summary,
        walk_forward_metadata,
        walk_forward_tickers,
    )


def build_equal_weight_curves(panel_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build one equal-weighted fold-return curve per strategy."""
    grouped = (
        panel_df.groupby(["agent", "fold_end"], as_index=False)
        .agg(
            period_return=("mean_actual_cumulative_return", "mean"),
            assets_in_fold=("ticker", "nunique"),
        )
        .sort_values(["agent", "fold_end"])
        .reset_index(drop=True)
    )

    curves: dict[str, pd.DataFrame] = {}
    for agent_name in AGENT_ORDER:
        agent_df = grouped.loc[grouped["agent"] == agent_name].copy()
        if agent_df.empty:
            continue
        safe_returns = agent_df["period_return"].clip(lower=-0.999999)
        agent_df["cumulative_return"] = np.expm1(np.log1p(safe_returns).cumsum())
        curves[agent_name] = agent_df
    return curves


def build_caption(curves: dict[str, pd.DataFrame], tickers: list[str], run_id: str) -> str:
    """Create a compact caption explaining the walk-forward curve construction."""
    summary_bits: list[str] = []
    for agent_name, curve_df in curves.items():
        final_return = float(curve_df["cumulative_return"].iloc[-1])
        summary_bits.append(f"{format_agent_name(agent_name)} {final_return:.3f}")

    ticker_text = ", ".join(tickers) if tickers else "current universe"
    return (
        f"{RESEARCH_TIMEFRAME_LABEL} walk-forward panel returns are compounded by fold end date. "
        f"Each step is the equal-weight mean out-of-sample panel return across available assets "
        f"for that fold end, so this is an equity-style summary of the current multi-asset run "
        f"rather than a broker-executable portfolio simulation. "
        f"Universe: {ticker_text}. Final compounded returns: {'; '.join(summary_bits)}. "
        f"Run ID: {run_id}."
    )


def main() -> None:
    """Plot the current run's multi-asset equity-style curves."""
    panel_df, panel_path = load_walk_forward_panel_summary()
    metadata = walk_forward_metadata(panel_path)
    run_id = str(metadata.get("run_id", "")).strip()
    tickers = walk_forward_tickers(panel_df, metadata)
    curves = build_equal_weight_curves(panel_df)
    if not curves:
        raise ValueError("No walk-forward equity-style curves could be built from the current run.")

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    y_min = 0.0
    y_max = 0.0
    for agent_name in AGENT_ORDER:
        curve_df = curves.get(agent_name)
        if curve_df is None or curve_df.empty:
            continue
        ax.plot(
            curve_df["fold_end"],
            curve_df["cumulative_return"],
            color=AGENT_COLORS.get(agent_name, "#355C7D"),
            linewidth=2.0,
            label=format_agent_name(agent_name),
        )
        y_min = min(y_min, float(curve_df["cumulative_return"].min()))
        y_max = max(y_max, float(curve_df["cumulative_return"].max()))

    ax.axhline(0.0, color=ZERO_LINE_COLOR, linewidth=0.9)
    apply_clean_style(
        ax,
        title="Multi-Asset Walk-Forward Equity Curves",
        x_label="Fold End Date",
        y_label="Compounded Equal-Weight Panel Return",
        show_y_grid=True,
        add_legend=True,
        legend_location="upper center",
        legend_ncol=3,
        legend_outside=True,
        legend_bbox_to_anchor=(0.5, -0.17),
    )
    apply_axis_number_format(ax)
    y_span = max(y_max - y_min, 0.5)
    y_padding = y_span * 0.14
    ax.set_ylim(
        min(y_min - y_padding, -y_padding * 0.25),
        max(y_max + y_padding, y_padding * 0.25),
    )

    add_figure_caption(fig, build_caption(curves, tickers, run_id))
    save_chart(fig, "multi_asset_walk_forward_equity_curve.png")
    show_chart()


if __name__ == "__main__":
    main()
