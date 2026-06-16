"""Combine walk-forward outputs across daily, 4-hour, and hourly runs."""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from artifact_provenance import write_dataframe_artifact
    from plot_config import apply_categorical_tick_labels, charts_dir, data_clean_dir
    from strategy_config import AGENT_ORDER
    from plot_config import format_agent_name
except ModuleNotFoundError:
    from Code.artifact_provenance import write_dataframe_artifact
    from Code.plot_config import apply_categorical_tick_labels, charts_dir, data_clean_dir
    from Code.strategy_config import AGENT_ORDER
    from Code.plot_config import format_agent_name


DEFAULT_INTERVALS = ("1d", "4h", "1h")
INTERVAL_LABELS = {
    "1d": "Daily",
    "4h": "4-Hour",
    "1h": "Hourly",
}
INTERVAL_COLORS = {
    "1d": "#4C78A8",
    "4h": "#F58518",
    "1h": "#54A24B",
}


def configured_intervals() -> list[str]:
    """Return the interval list for the frequency robustness summary."""
    raw_value = os.environ.get("FREQUENCY_ROBUSTNESS_INTERVALS", "").strip()
    if not raw_value:
        return list(DEFAULT_INTERVALS)
    return [value.strip().lower() for value in raw_value.split(",") if value.strip()]


def interval_clean_dir(interval: str) -> Path:
    """Return the clean-data directory for one interval."""
    if interval == "1d":
        return data_clean_dir()
    return data_clean_dir().with_name(f"{data_clean_dir().name}_{interval}")


def load_interval_outputs(interval: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load agent and panel walk-forward summaries for one interval."""
    clean_dir = interval_clean_dir(interval)
    agent_path = clean_dir / "multi_asset_walk_forward_agent_summary.csv"
    panel_path = clean_dir / "multi_asset_walk_forward_panel_summary.csv"
    if not agent_path.exists() or not panel_path.exists():
        raise FileNotFoundError(
            f"Missing walk-forward outputs for {interval}: {agent_path}, {panel_path}"
        )

    agent_df = pd.read_csv(agent_path)
    panel_df = pd.read_csv(panel_path)
    if agent_df.empty or panel_df.empty:
        raise ValueError(f"Empty walk-forward output for interval {interval}")
    return agent_df, panel_df


def build_agent_rows(interval: str, agent_df: pd.DataFrame, panel_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize one interval's agent-level output into the combined schema."""
    tickers = sorted(
        {
            str(value).strip().upper()
            for value in panel_df.get("ticker", pd.Series(dtype="object")).dropna()
            if str(value).strip()
        }
    )
    selected_columns = [
        "agent",
        "panel_count",
        "mean_mean_p_value",
        "mean_mean_actual_percentile",
        "mean_mean_RCSI_z",
        "proportion_significant_panels",
        "mean_proportion_outperforming_null_runs",
        "evidence_label",
        "verdict_label",
        "number_of_outer_runs",
        "simulations_per_run",
        "test_bars",
        "step_bars",
        "min_trades_per_panel",
    ]
    missing_columns = [column for column in selected_columns if column not in agent_df.columns]
    if missing_columns:
        raise KeyError(
            f"Missing columns in {interval} agent summary: {', '.join(missing_columns)}"
        )

    normalized = agent_df[selected_columns].copy()
    normalized.insert(0, "interval", interval)
    normalized.insert(1, "timeframe_label", INTERVAL_LABELS.get(interval, interval))
    normalized["ticker_count"] = len(tickers)
    normalized["tickers"] = ",".join(tickers)
    normalized = normalized.rename(
        columns={
            "mean_mean_p_value": "mean_p_value",
            "mean_mean_actual_percentile": "mean_actual_percentile",
            "mean_mean_RCSI_z": "mean_RCSI_z",
            "proportion_significant_panels": "significant_panel_rate",
            "mean_proportion_outperforming_null_runs": "outperform_rate",
        }
    )
    return normalized


def summarize_interval(agent_rows: pd.DataFrame, panel_df: pd.DataFrame) -> dict[str, object]:
    """Create one compact interval-level summary row."""
    best_row = agent_rows.loc[agent_rows["mean_actual_percentile"].astype(float).idxmax()]
    interval = str(agent_rows["interval"].iloc[0])
    return {
        "interval": interval,
        "timeframe_label": str(agent_rows["timeframe_label"].iloc[0]),
        "strategy_count": int(agent_rows["agent"].nunique()),
        "ticker_count": int(agent_rows["ticker_count"].iloc[0]),
        "panel_rows": int(len(panel_df)),
        "total_agent_panels": int(pd.to_numeric(agent_rows["panel_count"], errors="coerce").sum()),
        "min_strategy_mean_p_value": float(pd.to_numeric(agent_rows["mean_p_value"], errors="coerce").min()),
        "max_strategy_mean_percentile": float(best_row["mean_actual_percentile"]),
        "best_percentile_agent": str(best_row["agent"]),
        "mean_significant_panel_rate": float(
            pd.to_numeric(agent_rows["significant_panel_rate"], errors="coerce").mean()
        ),
        "mean_outperform_rate": float(
            pd.to_numeric(agent_rows["outperform_rate"], errors="coerce").mean()
        ),
        "number_of_outer_runs": int(agent_rows["number_of_outer_runs"].iloc[0]),
        "simulations_per_run": int(agent_rows["simulations_per_run"].iloc[0]),
        "test_bars": int(agent_rows["test_bars"].iloc[0]),
        "step_bars": int(agent_rows["step_bars"].iloc[0]),
        "min_trades_per_panel": int(agent_rows["min_trades_per_panel"].iloc[0]),
        "tickers": str(agent_rows["tickers"].iloc[0]),
    }


def combined_frequency_outputs(intervals: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build combined agent and interval summary tables."""
    agent_frames: list[pd.DataFrame] = []
    interval_rows: list[dict[str, object]] = []

    for interval in intervals:
        agent_df, panel_df = load_interval_outputs(interval)
        agent_rows = build_agent_rows(interval, agent_df, panel_df)
        agent_frames.append(agent_rows)
        interval_rows.append(summarize_interval(agent_rows, panel_df))

    combined_agent_df = pd.concat(agent_frames, ignore_index=True)
    combined_agent_df["agent"] = pd.Categorical(
        combined_agent_df["agent"],
        categories=AGENT_ORDER,
        ordered=True,
    )
    interval_order = {interval: index for index, interval in enumerate(intervals)}
    combined_agent_df["_interval_order"] = combined_agent_df["interval"].map(interval_order)
    combined_agent_df = (
        combined_agent_df.sort_values(["_interval_order", "agent"])
        .drop(columns=["_interval_order"])
        .reset_index(drop=True)
    )
    combined_agent_df["agent"] = combined_agent_df["agent"].astype(str)

    interval_summary_df = pd.DataFrame(interval_rows)
    interval_summary_df["_interval_order"] = interval_summary_df["interval"].map(interval_order)
    interval_summary_df = (
        interval_summary_df.sort_values("_interval_order")
        .drop(columns=["_interval_order"])
        .reset_index(drop=True)
    )
    return combined_agent_df, interval_summary_df


def plot_frequency_robustness(agent_df: pd.DataFrame, output_path: Path) -> None:
    """Plot mean p-values and percentiles by strategy and interval."""
    available_agents = [agent for agent in AGENT_ORDER if agent in set(agent_df["agent"])]
    intervals = [interval for interval in DEFAULT_INTERVALS if interval in set(agent_df["interval"])]
    intervals.extend(
        [
            interval
            for interval in agent_df["interval"].drop_duplicates().tolist()
            if interval not in intervals
        ]
    )
    if not available_agents or not intervals:
        raise ValueError("Cannot plot frequency robustness without agents and intervals.")

    x_positions = np.arange(len(available_agents), dtype=float)
    bar_width = min(0.22, 0.74 / max(len(intervals), 1))
    offset_center = (len(intervals) - 1) / 2.0

    fig, (ax_p, ax_pct) = plt.subplots(2, 1, figsize=(10.8, 8.2), sharex=True)
    for interval_index, interval in enumerate(intervals):
        interval_df = agent_df.loc[agent_df["interval"] == interval].set_index("agent")
        p_values = [
            float(interval_df.loc[agent, "mean_p_value"]) if agent in interval_df.index else np.nan
            for agent in available_agents
        ]
        percentiles = [
            float(interval_df.loc[agent, "mean_actual_percentile"]) if agent in interval_df.index else np.nan
            for agent in available_agents
        ]
        offset = (interval_index - offset_center) * bar_width
        label = INTERVAL_LABELS.get(interval, interval)
        color = INTERVAL_COLORS.get(interval, "#777777")
        ax_p.bar(x_positions + offset, p_values, width=bar_width, label=label, color=color)
        ax_pct.bar(x_positions + offset, percentiles, width=bar_width, label=label, color=color)

    ax_p.axhline(0.05, color="#B00020", linestyle="--", linewidth=1.0)
    ax_p.set_ylabel("Mean panel p-value")
    ax_p.set_ylim(0.0, min(1.0, max(0.75, float(agent_df["mean_p_value"].max()) * 1.15)))
    ax_p.grid(axis="y", alpha=0.35)
    ax_p.legend(frameon=False, ncols=len(intervals), loc="upper right")
    ax_p.set_title("Frequency robustness of the timing-skill null")

    ax_pct.axhline(50.0, color="#4F4F4F", linestyle="--", linewidth=1.0)
    ax_pct.set_ylabel("Mean actual percentile")
    ax_pct.set_ylim(0.0, 100.0)
    ax_pct.grid(axis="y", alpha=0.35)
    ax_pct.set_xticks(x_positions)
    apply_categorical_tick_labels(
        ax_pct,
        [format_agent_name(agent, short=True) for agent in available_agents],
        axis="x",
        fontsize=8.2,
    )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    intervals = configured_intervals()
    agent_df, interval_df = combined_frequency_outputs(intervals)

    agent_output_path = data_clean_dir() / "frequency_robustness_agent_summary.csv"
    interval_output_path = data_clean_dir() / "frequency_robustness_interval_summary.csv"
    chart_output_path = charts_dir() / "frequency_robustness_pvalue_percentile.png"

    write_dataframe_artifact(
        agent_df,
        agent_output_path,
        producer="frequency_robustness_summary.main",
        current_ticker="MULTI_FREQUENCY",
        research_grade=False,
        canonical_policy="auto",
        parameters={"intervals": intervals},
    )
    write_dataframe_artifact(
        interval_df,
        interval_output_path,
        producer="frequency_robustness_summary.main",
        current_ticker="MULTI_FREQUENCY",
        dependencies=[agent_output_path],
        research_grade=False,
        canonical_policy="auto",
        parameters={"intervals": intervals},
    )
    plot_frequency_robustness(agent_df, chart_output_path)

    print(f"[frequency] intervals: {', '.join(intervals)}")
    print(f"[frequency] rows: {len(agent_df)} agent rows, {len(interval_df)} interval rows")
    print(f"[frequency] wrote {agent_output_path}")
    print(f"[frequency] wrote {interval_output_path}")
    print(f"[frequency] wrote {chart_output_path}")
    print(interval_df.to_string(index=False))


if __name__ == "__main__":
    main()
