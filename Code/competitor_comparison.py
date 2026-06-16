"""Size and power of the structure-preserving null versus competitor tests.

Runs four tests on the SAME synthetic worlds (ground truth known), to show where
the structure-preserving null succeeds and where return-based tests fail:

  * SP   -- the structure-preserving timing null (this paper): randomize placement,
           hold the price path and trade geometry fixed.
  * Path -- a block-bootstrap return test: resample the return path with a circular
           moving-block bootstrap (block length 20) and replay the SAME realized
           schedule (Kunsch 1989; the block-bootstrap competitor the referee named).
  * RC   -- White's (2000) Reality Check, single-strategy specialization: a
           recentered stationary-bootstrap test of mean per-trade return vs benchmark 0.
  * SPA  -- Hansen's (2005) Superior Predictive Ability test, studentized variant.

The decisive world is ``structural_skill_absorbed'': the strategy is genuinely
profitable (drift x exposure) but has NO entry-placement skill (random placement).
A correct test of *timing* should not reject; a test of *profitability* (RC/SPA)
will. Output: Data_Clean/competitor_comparison.csv + Charts/competitor_comparison.png.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("TICKER", "GC=F")
os.environ.setdefault("MONTE_CARLO_SIMULATE_EXECUTION_COSTS", "0")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "Code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

import monte_carlo as mc
import synthetic_timing_experiments as syn

D = ROOT / "Data_Clean"
C = ROOT / "Charts"

REPLICATIONS = int(os.environ.get("CC_REPLICATIONS", "200"))
M_SIM = int(os.environ.get("CC_SIMULATIONS", "2000"))
B_BOOT = int(os.environ.get("CC_BOOT", "999"))
BLOCK_LEN = int(os.environ.get("CC_BLOCK_LEN", "20"))         # block length 20
BLOCK_Q = 1.0 / float(BLOCK_LEN)                              # stationary-bootstrap rate (RC/SPA)
ENTRY_SIGNAL = float(os.environ.get("CC_ENTRY_SIGNAL", "0.0035"))
ALPHA = 0.05

WORLDS = [
    ("iid_no_skill", 0.0, "IID, no skill"),
    ("drift_no_skill", 0.0, "Drift only, no skill"),
    ("vol_cluster_no_skill", 0.0, "Vol clustering, no skill"),
    ("structural_skill_absorbed", 0.0, "Structural exposure, no timing skill"),
    ("entry_skill", ENTRY_SIGNAL, "Genuine entry-placement skill"),
]


def stat_boot_idx(n, q, rng):
    new = rng.random(n) < q
    new[0] = True
    starts = rng.integers(0, n, size=n)
    idx = np.where(new, starts, 1)          # 1 = "advance previous"
    out = np.empty(n, dtype=np.int64)
    cur = 0
    for t in range(n):                      # light loop; n small for RC/SPA, ok for path
        cur = idx[t] if new[t] else (cur + 1) % n
        out[t] = cur
    return out


def build_world(world, signal, config, rng):
    """Mirror run_one's construction; return (open_prices, trade_structure)."""
    if world == "entry_skill":
        ts = syn.sample_random_structure(config, rng, duration_low=8, duration_high=9)
        r = syn.generate_returns(world, config.horizon_bars, rng, signal_strength=signal,
                                 trade_count=config.trade_count, event_starts=ts.entry_indices)
    elif world == "structural_skill_absorbed":
        r = syn.generate_returns(world, config.horizon_bars, rng, signal_strength=signal,
                                 trade_count=config.trade_count)
        ts = syn.sample_random_structure(config, rng, duration_low=16, duration_high=29)
    else:
        r = syn.generate_returns(world, config.horizon_bars, rng, signal_strength=signal,
                                 trade_count=config.trade_count)
        ts = syn.sample_random_structure(config, rng)
    return syn.build_price_path(r), ts


def sp_pvalue(open_prices, ts, rng):
    actual = syn.cumulative_return_for_structure(open_prices, ts)
    inputs = mc.NullModelInputs(
        open_price_matrix=open_prices.reshape(1, -1), trade_structure=ts,
        null_model_name="sp", calendar_dates=tuple(), context_entry_candidate_pools=tuple())
    sim = mc.simulate_structure_preserving_cumulative_returns(
        null_model_inputs=inputs, simulation_count=M_SIM, rng=rng).to_numpy(float)
    return mc.calculate_p_value(sim, actual)


def block_boot_idx(n, block_len, n_draws, rng):
    """Vectorized circular moving-block bootstrap: (n_draws, n) resampling indices."""
    n_blocks = int(np.ceil(n / block_len))
    starts = rng.integers(0, n, size=(n_draws, n_blocks))      # one start per block
    offsets = np.arange(block_len)
    idx = (starts[:, :, None] + offsets[None, None, :]).reshape(n_draws, n_blocks * block_len)
    return idx[:, :n] % n


def path_pvalue(returns, ts, actual, rng, start_price=100.0):
    """Block-bootstrap the return path (block length 20); replay the same schedule.

    Fully vectorized across the B resamples: build all price paths at once, then
    score the fixed trade structure on every path.
    """
    n = len(returns)
    idx = block_boot_idx(n, BLOCK_LEN, B_BOOT, rng)            # (B, n)
    rp = returns[idx]                                          # (B, n)
    op = np.empty((B_BOOT, n + 1), dtype=float)               # (B, n+1) price paths
    op[:, 0] = start_price
    op[:, 1:] = start_price * np.cumprod(1.0 + rp, axis=1)
    gross = op[:, ts.exit_indices] / op[:, ts.entry_indices] - 1.0
    log_r = np.log1p(gross * ts.position_value_fractions)     # (B, n_trades)
    sims = np.expm1(log_r.sum(axis=1))                        # (B,)
    return (1 + int(np.sum(sims >= actual))) / (B_BOOT + 1)


def per_trade_returns(open_prices, ts):
    g = open_prices[ts.exit_indices] / open_prices[ts.entry_indices] - 1.0
    return g * ts.position_value_fractions


def rc_spa_pvalues(d, rng):
    """Single-strategy Reality Check (recentered) and SPA (studentized) p-values."""
    n = len(d); dbar = d.mean(); sd = d.std(ddof=0)
    T_rc = np.sqrt(n) * dbar
    T_spa = T_rc / sd if sd > 0 else 0.0
    cnt_rc = cnt_spa = 0
    for b in range(B_BOOT):
        ds = d[stat_boot_idx(n, BLOCK_Q, rng)]
        rec = np.sqrt(n) * (ds.mean() - dbar)
        if rec >= T_rc:
            cnt_rc += 1
        sdb = ds.std(ddof=0)
        if sdb > 0 and rec / sdb >= T_spa:
            cnt_spa += 1
    return (1 + cnt_rc) / (B_BOOT + 1), (1 + cnt_spa) / (B_BOOT + 1)


def main():
    config = syn.SyntheticConfig()
    world_offset = {w: 100 * (i + 1) for i, (w, _, _) in enumerate(WORLDS)}  # deterministic
    rows = []
    for world, signal, label in WORLDS:
        rej = {"SP": 0, "Path": 0, "RC": 0, "SPA": 0}
        for rep in range(REPLICATIONS):
            seed = config.base_seed + rep * 7919 + world_offset[world]
            rng = np.random.default_rng(seed)
            op, ts = build_world(world, signal, config, rng)
            actual = syn.cumulative_return_for_structure(op, ts)
            returns = np.log(op[1:] / op[:-1])  # not used; path uses simple returns below
            returns = op[1:] / op[:-1] - 1.0
            d = per_trade_returns(op, ts)
            rng_sp = np.random.default_rng(seed + 17)
            rng_b = np.random.default_rng(seed + 29)
            p_sp = sp_pvalue(op, ts, rng_sp)
            p_path = path_pvalue(returns, ts, actual, rng_b)
            p_rc, p_spa = rc_spa_pvalues(d, np.random.default_rng(seed + 41))
            rej["SP"] += p_sp <= ALPHA
            rej["Path"] += p_path <= ALPHA
            rej["RC"] += p_rc <= ALPHA
            rej["SPA"] += p_spa <= ALPHA
        row = dict(world=world, label=label, signal=signal, replications=REPLICATIONS,
                   reject_SP=rej["SP"] / REPLICATIONS, reject_Path=rej["Path"] / REPLICATIONS,
                   reject_RC=rej["RC"] / REPLICATIONS, reject_SPA=rej["SPA"] / REPLICATIONS)
        rows.append(row)
        print(f"{label:<40} SP {row['reject_SP']:.3f}  Path {row['reject_Path']:.3f}  "
              f"RC {row['reject_RC']:.3f}  SPA {row['reject_SPA']:.3f}")
    df = pd.DataFrame(rows)
    df.to_csv(D / "competitor_comparison.csv", index=False)
    _chart(df)


def _chart(df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sys.path.insert(0, str(CODE))
    from pub_style import use_pub_style, BLUE, GREEN, GOLD, RED
    use_pub_style()
    methods = [("reject_SP", "Structure-preserving (timing)", BLUE),
               ("reject_Path", "Block bootstrap (path)", GREEN),
               ("reject_RC", "Reality Check (profit)", GOLD),
               ("reject_SPA", "SPA (profit)", RED)]
    x = np.arange(len(df)); w = 0.2
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    for i, (col, lab, c) in enumerate(methods):
        ax.bar(x + (i - 1.5) * w, df[col], w, color=c, label=lab, alpha=0.9)
    ax.axhline(0.05, color="#444", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(df["label"], rotation=18, ha="right", fontsize=8.5)
    ax.set_ylabel("rejection rate at 5\\%".replace("\\%", "%"))
    ax.set_ylim(0, 1.05)
    ax.set_title("Size and power vs. competitor tests across known-truth worlds")
    ax.legend(fontsize=8.5, ncol=2)
    fig.savefig(C / "competitor_comparison.png"); plt.close(fig)


if __name__ == "__main__":
    main()
