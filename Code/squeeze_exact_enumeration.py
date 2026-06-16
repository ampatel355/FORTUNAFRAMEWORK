"""Exact enumeration of the gap-permutation null orbit for the N=4 Squeeze Breakout.

The structure-preserving null draws a leading gap uniformly on {0,...,external_slack}
and a uniform permutation of the internal-gap multiset. The last exit is
permutation-invariant, so EVERY leading gap is feasible. The orbit is therefore
exactly (external_slack+1) * (number of permutations of the internal gaps). For
N=4 this is small enough to enumerate exactly, giving the exact attainable p-grid
and the exact one-sided tail probability, with no Monte Carlo error.

Faithfulness: the statistic is computed from the same committed open-price path and
the same deterministic cost convention as the canonical sampler
(calculate_directional_returns_from_open_prices - TRANSACTION_COST, then the
position-fraction weighting and multiplicative compounding). Deterministic costs are
used because an exact enumeration requires a deterministic statistic per schedule;
the published p=0.053 used the stochastic-fill model, so this run also reports a
deterministic-cost Monte Carlo estimate for cross-validation. No number is invented.
"""
from __future__ import annotations

import itertools
import os
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "Code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
os.environ.setdefault("TICKER", "GC=F")
os.environ["MONTE_CARLO_SIMULATE_EXECUTION_COSTS"] = "0"  # deterministic statistic

import monte_carlo as mc

TICKER = "GC=F"
AGENT = "volatility_squeeze_breakout"
DATA_CLEAN = PROJECT_ROOT / "Data_Clean"


def cumulative_return(entries: np.ndarray, exits: np.ndarray, open_prices: np.ndarray,
                      pos_fracs: np.ndarray, dirs: np.ndarray, cost: float) -> np.ndarray:
    """Vectorized deterministic-cost cumulative return for a batch of schedules.

    entries/exits: (B, N) int arrays of calendar indices. Returns (B,) cumulative returns.
    """
    entry_p = open_prices[entries]
    exit_p = open_prices[exits]
    long_r = (exit_p / entry_p) - 1.0
    short_r = (entry_p / exit_p) - 1.0
    gross = np.where(dirs[np.newaxis, :] > 0, long_r, short_r)
    net = gross - cost
    adjusted = pos_fracs[np.newaxis, :] * net
    return np.expm1(np.log1p(adjusted).sum(axis=1))


def main() -> None:
    market_df = mc.load_market_data(DATA_CLEAN / f"{TICKER}_regimes.csv")
    input_path = mc.ensure_trade_file_exists(TICKER, AGENT)
    trade_df = mc.load_trade_data(input_path, allow_empty=True)
    inputs = mc.prepare_agent_null_model_inputs(
        agent_name=AGENT, current_ticker=TICKER, trade_df=trade_df,
        market_df=market_df, input_path=input_path,
    )
    ts = inputs.trade_structure
    open_prices = inputs.open_price_matrix[0]
    max_open_index = open_prices.shape[0] - 1
    durations = ts.durations.astype(np.int64)
    internal_gaps = ts.internal_gap_sizes.astype(np.int64)
    slack = int(ts.external_slack)
    pos_fracs = ts.position_value_fractions.astype(float)
    dirs = ts.direction_signs.astype(float)
    n = len(durations)
    realized_lead = int(ts.entry_indices[0])
    cost = mc.TRANSACTION_COST

    print(f"agent={AGENT}  N={n}  durations={durations.tolist()}  internal_gaps={internal_gaps.tolist()}")
    print(f"external_slack={slack}  realized_leading_gap={realized_lead}  cost={cost}")

    perms = list(itertools.permutations(range(n - 1)))  # all (n-1)! orderings, with multiplicity
    leads = np.arange(0, slack + 1, dtype=np.int64)
    print(f"orbit size = {len(perms)} perms x {len(leads)} leads = {len(perms)*len(leads)}")

    # Build all schedules. entries[:,0]=lead; entries[:,j+1]=lead+cumsum(dur[:-1]+permgap)
    all_T = []
    realized_T = None
    for perm in perms:
        pgaps = internal_gaps[list(perm)]
        step = durations[:-1] + pgaps
        cum = np.cumsum(step)
        ent = np.empty((len(leads), n), dtype=np.int64)
        ent[:, 0] = leads
        ent[:, 1:] = leads[:, None] + cum[None, :]
        exi = ent + durations[None, :]
        assert exi[:, -1].max() <= max_open_index, "infeasible schedule found (should not happen)"
        T = cumulative_return(ent, exi, open_prices, pos_fracs, dirs, cost)
        all_T.append(T)
        if list(perm) == list(range(n - 1)):  # identity perm
            realized_T = float(T[realized_lead])
    all_T = np.concatenate(all_T)
    orbit = len(all_T)

    # exact one-sided tail probability under Q (perm-weighted, lead-uniform)
    q_exact = float(np.mean(all_T >= realized_T))
    distinct_T = int(np.unique(np.round(all_T, 10)).size)

    # cross-validation: deterministic-cost Monte Carlo estimate via the canonical sampler
    rng = mc.build_random_generator(reproducible=True, seed=mc.SEED)
    sim, _ = mc.simulate_agent_null_cumulative_returns(
        agent_name=AGENT, current_ticker=TICKER, trade_df=trade_df, market_df=market_df,
        input_path=input_path, simulation_count=20000, rng=rng,
    )
    sim_arr = sim.to_numpy(dtype=float)
    p_mc_detcost = mc.calculate_p_value(sim_arr, realized_T)

    print("\n=== EXACT ENUMERATION (deterministic-cost gap-permutation null) ===")
    print(f"realized T (deterministic-cost, open-price) = {realized_T:.6f}")
    print(f"orbit schedules enumerated                  = {orbit}")
    print(f"distinct attainable statistic values        = {distinct_T}")
    print(f"exact one-sided tail probability q_exact    = {q_exact:.6f}")
    print(f"  (with +1 correction (1+#>=)/(1+orbit)     = {(1+int(np.sum(all_T>=realized_T)))/(1+orbit):.6f})")
    print(f"deterministic-cost MC p (20000 draws, seed {mc.SEED}) = {p_mc_detcost:.6f}  [cross-check of q_exact]")
    print(f"grid resolution 1/orbit                      = {1.0/orbit:.2e}")


if __name__ == "__main__":
    main()
