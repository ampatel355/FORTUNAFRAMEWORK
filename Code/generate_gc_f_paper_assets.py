"""Generate publication-ready GC=F paper assets from the current run outputs."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker as mticker

try:
    from buy_and_hold import BUY_HOLD_TRANSACTION_COST
    from monte_carlo import load_trade_data
    from research_metrics import build_buy_and_hold_curve, build_daily_strategy_curve
    from strategy_config import AGENT_COLORS, AGENT_DISPLAY_NAMES, AGENT_ORDER, BENCHMARK_NAME
    from timeframe_config import normalize_timestamp_series
except ModuleNotFoundError:
    from Code.buy_and_hold import BUY_HOLD_TRANSACTION_COST
    from Code.monte_carlo import load_trade_data
    from Code.research_metrics import build_buy_and_hold_curve, build_daily_strategy_curve
    from Code.strategy_config import AGENT_COLORS, AGENT_DISPLAY_NAMES, AGENT_ORDER, BENCHMARK_NAME
    from Code.timeframe_config import normalize_timestamp_series


TICKER = "GC=F"
DATA_CLEAN_DIR = PROJECT_ROOT / "Data_Clean"
PAPER_ASSETS_DIR = PROJECT_ROOT / "PaperAssets"


def agent_label(agent_name: str) -> str:
    """Return a readable strategy label for paper charts."""
    if agent_name == "trend_momentum_verification":
        return "Validation Strategy (AVM)"
    return AGENT_DISPLAY_NAMES.get(agent_name, agent_name.replace("_", " ").title())


def percent_formatter(decimals: int = 0) -> mticker.FuncFormatter:
    """Format decimal returns as percentages."""
    return mticker.FuncFormatter(lambda value, _pos: f"{value * 100:.{decimals}f}%")


def load_market_df() -> pd.DataFrame:
    """Load the GC=F regime table used as the shared market calendar."""
    market_path = DATA_CLEAN_DIR / f"{TICKER}_regimes.csv"
    market_df = pd.read_csv(market_path, usecols=["Date", "Open", "Close"])
    market_df["Date"] = normalize_timestamp_series(market_df["Date"])
    market_df["Open"] = pd.to_numeric(market_df["Open"], errors="coerce")
    market_df["Close"] = pd.to_numeric(market_df["Close"], errors="coerce")
    market_df = market_df.dropna(subset=["Date", "Open", "Close"]).sort_values("Date").reset_index(drop=True)
    return market_df


def build_curves(market_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Reconstruct one daily curve per strategy plus the passive benchmark."""
    curves: dict[str, pd.DataFrame] = {}
    for agent_name in AGENT_ORDER:
        trade_path = DATA_CLEAN_DIR / f"{TICKER}_{agent_name}_trades.csv"
        trade_df = load_trade_data(trade_path, allow_empty=True)
        curves[agent_name] = build_daily_strategy_curve(trade_df, market_df)

    curves[BENCHMARK_NAME] = build_buy_and_hold_curve(
        market_df=market_df[["Date", "Close"]].copy(),
        transaction_cost=BUY_HOLD_TRANSACTION_COST,
    )
    return curves


def load_full_comparison() -> pd.DataFrame:
    """Load the strategy summary table used throughout the paper."""
    summary_df = pd.read_csv(DATA_CLEAN_DIR / f"{TICKER}_full_comparison.csv")
    summary_df["agent"] = summary_df["agent"].astype(str).str.strip()
    return summary_df


def load_monte_carlo_summary() -> pd.DataFrame:
    """Load the Monte Carlo summary table."""
    summary_df = pd.read_csv(DATA_CLEAN_DIR / f"{TICKER}_monte_carlo_summary.csv")
    summary_df["agent"] = summary_df["agent"].astype(str).str.strip()
    return summary_df


def configure_axis(ax) -> None:
    """Apply a restrained publication style."""
    ax.grid(axis="y", color="#D6DCE3", linewidth=0.8, alpha=0.85)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#2E2E2E")
    ax.spines["bottom"].set_color("#2E2E2E")
    ax.tick_params(colors="#222222", labelsize=9)
    ax.title.set_color("#222222")
    ax.xaxis.label.set_color("#222222")
    ax.yaxis.label.set_color("#222222")


def save_figure(fig: plt.Figure, filename: str) -> None:
    """Save one paper asset with consistent export settings."""
    PAPER_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PAPER_ASSETS_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def create_cumulative_return_bar_chart(summary_df: pd.DataFrame) -> None:
    """Create a split-panel cumulative-return figure with benchmark context."""
    active_df = summary_df.loc[summary_df["agent"] != BENCHMARK_NAME].copy()
    active_df = active_df.sort_values("cumulative_return", ascending=False).reset_index(drop=True)
    benchmark_row = summary_df.loc[summary_df["agent"] == BENCHMARK_NAME].iloc[0]

    fig = plt.figure(figsize=(11.5, 6.8))
    grid = fig.add_gridspec(1, 2, width_ratios=[5.8, 1.4], wspace=0.18)
    ax_active = fig.add_subplot(grid[0, 0])
    ax_benchmark = fig.add_subplot(grid[0, 1])

    x_positions = np.arange(len(active_df))
    active_colors = [AGENT_COLORS.get(agent, "#355C7D") for agent in active_df["agent"]]
    ax_active.bar(
        x_positions,
        active_df["cumulative_return"].to_numpy(dtype=float),
        color=active_colors,
        edgecolor="#2E2E2E",
        linewidth=0.6,
        width=0.65,
    )
    ax_active.axhline(0.0, color="#4F4F4F", linewidth=0.9)
    ax_active.set_xticks(x_positions)
    ax_active.set_xticklabels(
        [agent_label(agent) for agent in active_df["agent"]],
        rotation=26,
        ha="right",
        fontsize=9,
    )
    ax_active.yaxis.set_major_formatter(percent_formatter())
    ax_active.set_ylabel("Cumulative return")
    ax_active.set_title("Active strategies and random baseline")
    configure_axis(ax_active)

    benchmark_value = float(benchmark_row["cumulative_return"])
    ax_benchmark.bar(
        [0],
        [benchmark_value],
        color=AGENT_COLORS[BENCHMARK_NAME],
        edgecolor="#2E2E2E",
        linewidth=0.6,
        width=0.55,
    )
    ax_benchmark.set_xticks([0])
    ax_benchmark.set_xticklabels(["Buy and Hold"], rotation=18, ha="right", fontsize=9)
    ax_benchmark.yaxis.set_major_formatter(percent_formatter())
    ax_benchmark.set_title("Passive benchmark")
    configure_axis(ax_benchmark)

    active_upper = max(0.95, float(active_df["cumulative_return"].max()) * 1.15)
    ax_active.set_ylim(min(-0.12, float(active_df["cumulative_return"].min()) * 1.25), active_upper)
    ax_benchmark.set_ylim(0.0, benchmark_value * 1.08)

    fig.suptitle(
        "Gold futures cumulative returns: active rules versus passive exposure",
        fontsize=13,
        color="#222222",
        y=1.02,
    )
    fig.text(
        0.5,
        -0.02,
        (
            "The benchmark is separated into its own panel so the active strategies remain legible. "
            "This is the visual version of the paper's core point: many rules made money, but most "
            "did not demonstrate timing skill once compared with structure-matched randomness."
        ),
        ha="center",
        va="top",
        fontsize=9,
        color="#3C4A59",
    )

    save_figure(fig, "gold_cumulative_return_bar_chart.png")


def create_pvalue_percentile_chart(summary_df: pd.DataFrame) -> None:
    """Create a side-by-side p-value and percentile comparison chart."""
    strategy_df = summary_df.loc[summary_df["agent"] != BENCHMARK_NAME].copy()
    strategy_df = strategy_df.sort_values(["actual_percentile", "p_value"], ascending=[False, True]).reset_index(drop=True)
    y_positions = np.arange(len(strategy_df))
    colors = [AGENT_COLORS.get(agent, "#355C7D") for agent in strategy_df["agent"]]

    fig, (ax_p, ax_pct) = plt.subplots(
        1,
        2,
        figsize=(12.8, 7.8),
        sharey=True,
        gridspec_kw={"wspace": 0.06, "width_ratios": [1.0, 1.0]},
    )

    ax_p.barh(
        y_positions,
        strategy_df["p_value"].to_numpy(dtype=float),
        color=colors,
        edgecolor="#2E2E2E",
        linewidth=0.6,
        height=0.64,
    )
    ax_p.axvline(0.05, color="#D62728", linestyle="--", linewidth=1.1)
    ax_p.set_xlabel("Monte Carlo p-value")
    ax_p.set_xlim(0.0, 1.0)
    configure_axis(ax_p)

    ax_pct.barh(
        y_positions,
        strategy_df["actual_percentile"].to_numpy(dtype=float),
        color=colors,
        edgecolor="#2E2E2E",
        linewidth=0.6,
        height=0.64,
    )
    ax_pct.axvline(70.0, color="#8A6D1D", linestyle=":", linewidth=1.0)
    ax_pct.axvline(85.0, color="#2E7D32", linestyle="--", linewidth=1.0)
    ax_pct.axvline(95.0, color="#1B5E20", linestyle="-.", linewidth=1.0)
    ax_pct.set_xlabel("Actual percentile in null distribution")
    ax_pct.set_xlim(0.0, 100.0)
    ax_pct.xaxis.set_major_formatter(mticker.FuncFormatter(lambda value, _pos: f"{value:.0f}"))
    configure_axis(ax_pct)

    ax_p.set_yticks(y_positions)
    ax_p.set_yticklabels([agent_label(agent) for agent in strategy_df["agent"]], fontsize=9)
    ax_pct.tick_params(axis="y", labelleft=False)
    ax_p.invert_yaxis()

    fig.suptitle(
        "Timing evidence by strategy: p-values and percentile rank",
        fontsize=13,
        color="#222222",
        y=1.01,
    )
    fig.text(
        0.5,
        -0.02,
        (
            "Lower p-values and higher percentile ranks indicate stronger timing evidence. "
            "No strategy reaches the paper's moderate-skill requirement of p <= 0.05, even when "
            "some percentile readings appear favorable."
        ),
        ha="center",
        va="top",
        fontsize=9,
        color="#3C4A59",
    )

    save_figure(fig, "gold_pvalue_percentile_comparison.png")


def create_drawdown_chart(curves: dict[str, pd.DataFrame]) -> None:
    """Create drawdown curves for all strategies plus buy-and-hold."""
    fig, ax = plt.subplots(figsize=(11.8, 7.4))
    plot_order = AGENT_ORDER + [BENCHMARK_NAME]

    for agent_name in plot_order:
        curve_df = curves[agent_name]
        linewidth = 2.3 if agent_name == BENCHMARK_NAME else 1.4
        alpha = 0.95 if agent_name == BENCHMARK_NAME else 0.88
        ax.plot(
            curve_df["Date"],
            curve_df["drawdown"].to_numpy(dtype=float),
            color=AGENT_COLORS.get(agent_name, "#355C7D"),
            linewidth=linewidth,
            alpha=alpha,
            label=agent_label(agent_name),
        )

    ax.axhline(0.0, color="#4F4F4F", linewidth=0.9)
    ax.yaxis.set_major_formatter(percent_formatter())
    ax.set_ylabel("Drawdown from prior peak")
    ax.set_xlabel("Date")
    ax.set_title("Gold futures drawdown curves by strategy and benchmark")
    configure_axis(ax)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=3,
        frameon=False,
        fontsize=8.4,
    )

    fig.text(
        0.5,
        -0.04,
        (
            "The benchmark drawdown is the deepest in absolute terms, but several active strategies "
            "also experience meaningful losses without delivering decisive timing evidence."
        ),
        ha="center",
        va="top",
        fontsize=9,
        color="#3C4A59",
    )

    save_figure(fig, "gold_drawdown_curves.png")


def create_donchian_histogram(monte_carlo_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    """Create a publication-ready Monte Carlo histogram for the Donchian example."""
    agent_name = "donchian_trend_reentry"
    results_path = DATA_CLEAN_DIR / f"{TICKER}_{agent_name}_monte_carlo_results.csv"
    simulated_df = pd.read_csv(results_path)
    simulated_returns = simulated_df["simulated_cumulative_return"].to_numpy(dtype=float)
    summary_row = monte_carlo_df.loc[monte_carlo_df["agent"] == agent_name].iloc[0]
    actual_return = float(summary_row["actual_cumulative_return"])
    mean_return = float(summary_row["mean_simulated_return"])
    median_return = float(summary_row["median_simulated_return"])

    fig, ax = plt.subplots(figsize=(9.0, 6.6))
    ax.hist(
        simulated_returns,
        bins=36,
        color="#AEC7E8",
        edgecolor="#2E2E2E",
        linewidth=0.55,
        alpha=0.95,
    )
    ax.axvline(actual_return, color="#D62728", linewidth=2.0, label="Actual return")
    ax.axvline(mean_return, color="#1F77B4", linewidth=1.6, linestyle="--", label="Null mean")
    ax.axvline(median_return, color="#2CA02C", linewidth=1.4, linestyle=":", label="Null median")
    ax.xaxis.set_major_formatter(percent_formatter())
    ax.set_xlabel("Cumulative return")
    ax.set_ylabel("Simulation count")
    ax.set_title("Donchian Trend Reentry under the structure-preserving null")
    configure_axis(ax)
    ax.legend(frameon=False, fontsize=9)

    fig.text(
        0.5,
        -0.02,
        (
            "Donchian Trend Reentry is profitable in absolute terms, but the actual result lies below "
            "the center of its matched random-timing distribution. This is the paper's clearest "
            "example of why profit alone is not evidence of timing skill."
        ),
        ha="center",
        va="top",
        fontsize=9,
        color="#3C4A59",
    )

    save_figure(fig, "gold_donchian_monte_carlo.png")


def main() -> None:
    """Build all paper-specific GC=F visual assets."""
    market_df = load_market_df()
    curves = build_curves(market_df)
    full_comparison_df = load_full_comparison()
    monte_carlo_summary_df = load_monte_carlo_summary()

    create_cumulative_return_bar_chart(full_comparison_df)
    create_pvalue_percentile_chart(full_comparison_df)
    create_drawdown_chart(curves)
    create_donchian_histogram(monte_carlo_summary_df, full_comparison_df)


if __name__ == "__main__":
    main()
