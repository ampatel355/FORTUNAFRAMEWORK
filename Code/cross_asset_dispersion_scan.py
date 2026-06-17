"""Path-degeneracy (near-zero null dispersion) scan across the cross-asset panel.

The limitation in the paper notes that for short-duration templates on near-flat
price paths, the structure-preserving null distribution can have near-zero
dispersion, which makes the percentile sensitive to negligible return differences.
This script quantifies how often that actually happens across the full 322-test
cross-asset panel, using only committed artifacts -- no Monte Carlo is re-run.

The null dispersion is recovered exactly from the two persisted columns, since
    RCSI   = actual_cumulative_return - mean_simulated_return
    RCSI_z = (actual_cumulative_return - mean_simulated_return) / std_simulated_return
so the realized null dispersion is the algebraic identity
    std_simulated_return = RCSI / RCSI_z      (for RCSI_z != 0).

A test is flagged PATH-DEGENERATE when its recovered null dispersion falls below a
documented floor in cumulative-return units. We report counts at two floors and,
critically, whether any flagged test is a multiple-testing discovery (it is not).

Reads:  Data_Clean/<ASSET>_full_comparison.csv  (one row per strategy per asset)
Writes: Data_Clean/cross_asset_dispersion_scan.csv  (per-test null dispersion + flag)
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_CLEAN = PROJECT_ROOT / "Data_Clean"

FDR = 0.05
# Dispersion floors in cumulative-return units. The primary floor (0.01) is ~30x
# below the panel median dispersion; the tighter floor (0.005) isolates the most
# severe cases. Both are reported so the count is not threshold-fragile.
PRIMARY_FLOOR = 0.01
TIGHT_FLOOR = 0.005


def main() -> None:
    rows = []
    for f in sorted(glob.glob(str(DATA_CLEAN / "*_full_comparison.csv"))):
        asset = os.path.basename(f).replace("_full_comparison.csv", "")
        df = pd.read_csv(f)
        if "p_value" not in df.columns:
            continue
        for _, r in df.iterrows():
            if pd.isna(r.get("p_value")):
                continue
            rows.append(dict(
                asset=asset,
                agent=str(r.get("agent")),
                RCSI=float(r.get("RCSI", np.nan)),
                RCSI_z=float(r.get("RCSI_z", np.nan)),
                p_value=float(r.get("p_value")),
                actual_percentile=float(r.get("actual_percentile", np.nan)),
                number_of_trades=r.get("number_of_trades"),
            ))

    P = pd.DataFrame(rows)
    m = len(P)

    # Recover the realized null dispersion exactly from the persisted statistics.
    with np.errstate(divide="ignore", invalid="ignore"):
        P["null_dispersion"] = np.where(
            P["RCSI_z"] != 0, P["RCSI"] / P["RCSI_z"], np.nan
        )
    disp = P["null_dispersion"].abs()
    P["abs_null_dispersion"] = disp
    P["path_degenerate"] = disp < PRIMARY_FLOOR

    # Bonferroni discovery flag, to confirm degenerate tests are not discoveries.
    bonf = FDR / m
    P["bonferroni_significant"] = P["p_value"] <= bonf

    P = P.sort_values("abs_null_dispersion").reset_index(drop=True)
    P.to_csv(DATA_CLEAN / "cross_asset_dispersion_scan.csv", index=False)

    n_primary = int((disp < PRIMARY_FLOOR).sum())
    n_tight = int((disp < TIGHT_FLOOR).sum())
    n_zero = int((P["RCSI_z"] == 0).sum())
    n_nan = int(P["null_dispersion"].isna().sum())
    degen = P[P["path_degenerate"]]
    n_degen_discoveries = int(degen["bonferroni_significant"].sum())

    print("=== Cross-asset null-dispersion (path-degeneracy) scan ===")
    print(f"tests                          : {m}")
    print(f"exactly-zero dispersion        : {n_zero}  (RCSI_z == 0)")
    print(f"undefined dispersion (NaN)     : {n_nan}")
    print(f"panel median |dispersion|      : {disp.median():.4f}")
    print(f"panel min |dispersion|         : {disp.min():.5f}")
    print(f"path-degenerate < {PRIMARY_FLOOR:<6}      : {n_primary}")
    print(f"path-degenerate < {TIGHT_FLOOR:<6}     : {n_tight}")
    print(f"  of which Bonferroni discoveries: {n_degen_discoveries}")
    print("\nlowest-dispersion tests:")
    cols = ["asset", "agent", "RCSI", "RCSI_z", "abs_null_dispersion",
            "actual_percentile", "p_value", "number_of_trades"]
    print(P.head(10)[cols].to_string(index=False))


if __name__ == "__main__":
    main()
