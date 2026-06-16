"""Compare the structure-preserving timing null with simpler return nulls."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "Code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib"))
os.environ.setdefault("MONTE_CARLO_SIMULATE_EXECUTION_COSTS", "0")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import monte_carlo
from artifact_provenance import write_dataframe_artifact
from research_metrics import calculate_p_value_prominence
from strategy_config import AGENT_ORDER, AGENT_SHORT_DISPLAY_NAMES


@dataclass(frozen=True)
class BenchmarkConfig:
    ticker: str = os.environ.get("NULL_BENCHMARK_TICKER", "GC=F").strip()
    simulations: int = int(os.environ.get("NULL_BENCHMARK_SIMULATIONS", "5000"))
    seed: int = int(os.environ.get("NULL_BENCHMARK_SEED", "20260526"))
    stationary_mean_block_bars: int = int(
        os.environ.get("NULL_BENCHMARK_STATIONARY_MEAN_BLOCK_BARS", "20")
    )
    batch_size: int = int(os.environ.get("NULL_BENCHMARK_BATCH_SIZE", "256"))


METHOD_METADATA = {
    "structure_preserving_schedule": {
        "label": "Structure-preserving schedule",
        "preserves_price_path": True,
        "preserves_trade_geometry": True,
        "controls_data_snooping": False,
        "tests_entry_placement": True,
        "description": "Randomizes calendar placement while preserving realized trade geometry.",
    },
    "shuffled_returns": {
        "label": "Shuffled returns",
        "preserves_price_path": False,
        "preserves_trade_geometry": True,
        "controls_data_snooping": False,
        "tests_entry_placement": False,
        "description": "Replays realized trades on an iid permutation of open-to-open returns.",
    },
    "stationary_bootstrap_returns": {
        "label": "Stationary bootstrap returns",
        "preserves_price_path": False,
        "preserves_trade_geometry": True,
        "controls_data_snooping": False,
        "tests_entry_placement": False,
        "description": "Replays realized trades on stationary-bootstrap return paths.",
    },
}


def load_market_df(data_clean_dir: Path, ticker: str) -> pd.DataFrame:
    """Load the market calendar used for the benchmark."""
    market_path = data_clean_dir / f"{ticker}_regimes.csv"
    return monte_carlo.load_market_data(market_path)


def calculate_actual_cumulative_return(trade_df: pd.DataFrame, input_path: Path) -> float:
    """Calculate the realized cumulative return using the project convention."""
    adjusted_returns = monte_carlo.adjust_trade_returns(
        raw_returns=trade_df["return"].to_numpy(dtype=float),
        transaction_cost=monte_carlo.TRANSACTION_COST,
        input_path=input_path,
    )
    log_returns = monte_carlo.convert_to_log_returns(adjusted_returns)
    return monte_carlo.calculate_cumulative_return_from_log_returns(log_returns)


def sample_shuffled_return_paths(
    one_period_returns: np.ndarray,
    *,
    sample_count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample return paths by independently shuffling the observed returns."""
    permutation_keys = rng.random((sample_count, len(one_period_returns)))
    permutation_indices = np.argsort(permutation_keys, axis=1)
    return one_period_returns[permutation_indices]


def sample_stationary_bootstrap_return_paths(
    one_period_returns: np.ndarray,
    *,
    sample_count: int,
    mean_block_bars: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample stationary-bootstrap return paths with geometric block lengths."""
    if mean_block_bars <= 0:
        raise ValueError("Mean block length must be positive.")
    period_count = len(one_period_returns)
    if period_count <= 0:
        raise ValueError("Cannot bootstrap an empty return series.")

    restart_probability = 1.0 / float(mean_block_bars)
    sampled_indices = np.empty((sample_count, period_count), dtype=np.int64)
    sampled_indices[:, 0] = rng.integers(0, period_count, size=sample_count)
    for column in range(1, period_count):
        restart_mask = rng.random(sample_count) < restart_probability
        continued = (sampled_indices[:, column - 1] + 1) % period_count
        restarted = rng.integers(0, period_count, size=sample_count)
        sampled_indices[:, column] = np.where(restart_mask, restarted, continued)

    return one_period_returns[sampled_indices]


def replay_trade_geometry_on_return_paths(
    sampled_returns: np.ndarray,
    trade_structure: monte_carlo.TradeStructure,
) -> np.ndarray:
    """Price realized trade intervals on synthetic return paths."""
    cumulative_log_returns = np.concatenate(
        [
            np.zeros((sampled_returns.shape[0], 1), dtype=float),
            np.cumsum(np.log1p(sampled_returns), axis=1),
        ],
        axis=1,
    )
    interval_log_returns = (
        cumulative_log_returns[:, trade_structure.exit_indices]
        - cumulative_log_returns[:, trade_structure.entry_indices]
    )
    long_returns = np.expm1(interval_log_returns)
    short_returns = np.expm1(-interval_log_returns)
    position_returns = np.where(
        trade_structure.direction_signs[np.newaxis, :] > 0,
        long_returns,
        short_returns,
    )
    net_position_returns = position_returns - monte_carlo.TRANSACTION_COST
    adjusted_returns = (
        net_position_returns
        * trade_structure.position_value_fractions[np.newaxis, :]
    )
    if np.any(adjusted_returns <= -1):
        raise ValueError("A benchmark null produced a trade return below -100%.")
    return np.expm1(np.log1p(adjusted_returns).sum(axis=1))


def simulate_return_resample_null(
    *,
    one_period_returns: np.ndarray,
    trade_structure: monte_carlo.TradeStructure,
    simulation_count: int,
    batch_size: int,
    rng: np.random.Generator,
    method: str,
    stationary_mean_block_bars: int,
) -> pd.Series:
    """Simulate shuffled-return or stationary-bootstrap null returns."""
    simulated = np.empty(simulation_count, dtype=float)
    for batch_start in range(0, simulation_count, batch_size):
        current_batch = min(batch_size, simulation_count - batch_start)
        if method == "shuffled_returns":
            sampled_returns = sample_shuffled_return_paths(
                one_period_returns,
                sample_count=current_batch,
                rng=rng,
            )
        elif method == "stationary_bootstrap_returns":
            sampled_returns = sample_stationary_bootstrap_return_paths(
                one_period_returns,
                sample_count=current_batch,
                mean_block_bars=stationary_mean_block_bars,
                rng=rng,
            )
        else:
            raise ValueError(f"Unknown return-resampling method: {method}")

        simulated[batch_start : batch_start + current_batch] = (
            replay_trade_geometry_on_return_paths(sampled_returns, trade_structure)
        )

    return pd.Series(simulated, name="simulated_cumulative_return")


def build_result_row(
    *,
    config: BenchmarkConfig,
    agent_name: str,
    method: str,
    actual_cumulative_return: float,
    simulated_returns: pd.Series,
    trade_count: int,
) -> dict[str, float | int | str | bool]:
    """Build one strategy-method benchmark row."""
    simulated_array = simulated_returns.to_numpy(dtype=float)
    p_value = monte_carlo.calculate_p_value(simulated_array, actual_cumulative_return)
    metadata = METHOD_METADATA[method]
    return {
        "ticker": config.ticker,
        "agent": agent_name,
        "strategy_label": AGENT_SHORT_DISPLAY_NAMES.get(agent_name, agent_name),
        "method": method,
        "method_label": metadata["label"],
        "preserves_price_path": metadata["preserves_price_path"],
        "preserves_trade_geometry": metadata["preserves_trade_geometry"],
        "controls_data_snooping": metadata["controls_data_snooping"],
        "tests_entry_placement": metadata["tests_entry_placement"],
        "actual_cumulative_return": actual_cumulative_return,
        "mean_null_return": float(np.mean(simulated_array)),
        "median_null_return": float(np.median(simulated_array)),
        "lower_5pct": float(np.percentile(simulated_array, 5)),
        "upper_95pct": float(np.percentile(simulated_array, 95)),
        "p_value": p_value,
        "actual_percentile": monte_carlo.calculate_actual_percentile(
            simulated_array,
            actual_cumulative_return,
        ),
        "p_value_prominence": calculate_p_value_prominence(p_value),
        "evidence_label": monte_carlo.interpret_p_value(p_value),
        "reject_0_05": bool(p_value <= 0.05),
        "number_of_trades": trade_count,
        "simulation_count": config.simulations,
        "transaction_cost": monte_carlo.TRANSACTION_COST,
        "stationary_mean_block_bars": (
            config.stationary_mean_block_bars
            if method == "stationary_bootstrap_returns"
            else ""
        ),
        "method_description": metadata["description"],
    }


def run_agent_benchmarks(
    *,
    config: BenchmarkConfig,
    agent_name: str,
    market_df: pd.DataFrame,
    data_clean_dir: Path,
    seed_sequence: np.random.SeedSequence,
) -> list[dict[str, float | int | str | bool]]:
    """Run all benchmark nulls for one strategy."""
    input_path = data_clean_dir / f"{config.ticker}_{agent_name}_trades.csv"
    trade_df = monte_carlo.load_trade_data(input_path, allow_empty=True)
    if trade_df.empty:
        return []

    actual_cumulative_return = calculate_actual_cumulative_return(trade_df, input_path)
    null_model_inputs = monte_carlo.prepare_agent_null_model_inputs(
        agent_name=agent_name,
        current_ticker=config.ticker,
        trade_df=trade_df,
        market_df=market_df,
        input_path=input_path,
    )
    one_period_returns = (
        market_df["Open"].to_numpy(dtype=float)[1:]
        / market_df["Open"].to_numpy(dtype=float)[:-1]
    ) - 1.0

    child_sequences = seed_sequence.spawn(3)
    method_returns = {
        "structure_preserving_schedule": monte_carlo.simulate_structure_preserving_cumulative_returns(
            null_model_inputs=null_model_inputs,
            simulation_count=config.simulations,
            rng=np.random.default_rng(child_sequences[0]),
        ),
        "shuffled_returns": simulate_return_resample_null(
            one_period_returns=one_period_returns,
            trade_structure=null_model_inputs.trade_structure,
            simulation_count=config.simulations,
            batch_size=config.batch_size,
            rng=np.random.default_rng(child_sequences[1]),
            method="shuffled_returns",
            stationary_mean_block_bars=config.stationary_mean_block_bars,
        ),
        "stationary_bootstrap_returns": simulate_return_resample_null(
            one_period_returns=one_period_returns,
            trade_structure=null_model_inputs.trade_structure,
            simulation_count=config.simulations,
            batch_size=config.batch_size,
            rng=np.random.default_rng(child_sequences[2]),
            method="stationary_bootstrap_returns",
            stationary_mean_block_bars=config.stationary_mean_block_bars,
        ),
    }

    return [
        build_result_row(
            config=config,
            agent_name=agent_name,
            method=method,
            actual_cumulative_return=actual_cumulative_return,
            simulated_returns=simulated_returns,
            trade_count=len(trade_df),
        )
        for method, simulated_returns in method_returns.items()
    ]


def add_method_level_bh_adjustments(results_df: pd.DataFrame) -> pd.DataFrame:
    """Add BH-adjusted p-values within each method family."""
    adjusted = results_df.copy()
    adjusted["bh_adjusted_p_value"] = np.nan
    for method, method_df in adjusted.groupby("method", sort=False):
        adjusted.loc[method_df.index, "bh_adjusted_p_value"] = (
            monte_carlo.benjamini_hochberg_adjusted_p_values(method_df["p_value"])
        )
    return adjusted


def create_method_comparison_plot(results_df: pd.DataFrame, output_path: Path) -> None:
    """Save a p-value comparison chart across benchmark nulls."""
    pivot_df = results_df.pivot(index="strategy_label", columns="method", values="p_value")
    order = (
        results_df.loc[results_df["method"] == "structure_preserving_schedule"]
        .sort_values("p_value")
        ["strategy_label"]
        .tolist()
    )
    pivot_df = pivot_df.loc[order]

    method_order = [
        "structure_preserving_schedule",
        "shuffled_returns",
        "stationary_bootstrap_returns",
    ]
    method_colors = {
        "structure_preserving_schedule": "#D62728",
        "shuffled_returns": "#355C7D",
        "stationary_bootstrap_returns": "#2A9D8F",
    }
    method_markers = {
        "structure_preserving_schedule": "o",
        "shuffled_returns": "s",
        "stationary_bootstrap_returns": "^",
    }

    x_positions = np.arange(len(pivot_df))
    fig, ax = plt.subplots(figsize=(11.8, 5.8))
    for method in method_order:
        ax.plot(
            x_positions,
            pivot_df[method].clip(lower=1e-4).to_numpy(dtype=float),
            marker=method_markers[method],
            linewidth=1.8,
            markersize=5.5,
            color=method_colors[method],
            label=str(METHOD_METADATA[method]["label"]),
        )

    ax.axhline(0.05, color="#4F4F4F", linestyle="--", linewidth=1.1)
    ax.text(
        len(pivot_df) - 0.4,
        0.052,
        "5% threshold",
        ha="right",
        va="bottom",
        fontsize=8.5,
        color="#4F4F4F",
    )
    ax.set_yscale("log")
    ax.set_ylim(1e-4, 1.05)
    ax.set_ylabel("One-sided p-value (log scale)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(pivot_df.index.tolist(), rotation=28, ha="right")
    ax.set_title("Null-method comparison on GC=F strategy panel")
    ax.grid(axis="y", color="#D6DCE3", linewidth=0.8, alpha=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, ncol=3, loc="upper center")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Run the benchmark comparison and save CSV plus chart artifacts."""
    config = BenchmarkConfig()
    monte_carlo.SIMULATE_EXECUTION_COSTS = False

    data_clean_dir = PROJECT_ROOT / "Data_Clean"
    charts_dir = PROJECT_ROOT / "Charts"
    market_df = load_market_df(data_clean_dir, config.ticker)

    seed_sequence = np.random.SeedSequence(config.seed)
    agent_sequences = seed_sequence.spawn(len(AGENT_ORDER))
    rows: list[dict[str, float | int | str | bool]] = []
    for agent_name, agent_seed_sequence in zip(AGENT_ORDER, agent_sequences):
        rows.extend(
            run_agent_benchmarks(
                config=config,
                agent_name=agent_name,
                market_df=market_df,
                data_clean_dir=data_clean_dir,
                seed_sequence=agent_seed_sequence,
            )
        )

    results_df = add_method_level_bh_adjustments(pd.DataFrame(rows))
    output_path = data_clean_dir / "null_benchmark_comparison.csv"
    chart_path = charts_dir / "null_method_comparison.png"

    write_result = write_dataframe_artifact(
        results_df,
        output_path,
        producer="null_benchmark_comparison.main",
        current_ticker=config.ticker,
        dependencies=[
            data_clean_dir / f"{config.ticker}_regimes.csv",
            *[data_clean_dir / f"{config.ticker}_{agent_name}_trades.csv" for agent_name in AGENT_ORDER],
        ],
        research_grade=config.simulations >= 5000,
        canonical_policy="auto",
        parameters=config.__dict__,
    )
    create_method_comparison_plot(results_df, chart_path)

    aggregate = (
        results_df.groupby(["method", "method_label"], sort=False)
        .agg(
            mean_p_value=("p_value", "mean"),
            median_p_value=("p_value", "median"),
            rejections_0_05=("reject_0_05", "sum"),
        )
        .reset_index()
    )
    print(aggregate.to_string(index=False))
    print(f"\nSaved null benchmark comparison to {write_result['versioned_path']}")
    print(f"Saved null benchmark chart to {chart_path}")
    if write_result["canonical_updated"]:
        print(f"Updated canonical benchmark at {output_path}")


if __name__ == "__main__":
    main()
