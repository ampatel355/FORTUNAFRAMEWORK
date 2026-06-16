# Fortuna — Structure-Preserving Randomization Inference for Decision Timing

Replication code and derived data for:

> Aryan Patel. *Structure-Preserving Randomization Inference for Decision Timing.*
> Submitted to **Risks** (MDPI).
> Archived: https://github.com/ampatel355/FORTUNAFRAMEWORK · DOI: https://doi.org/10.5281/zenodo.20695539

## Overview

This repository reproduces every table and figure in the paper and its Online
Supplement. The method is **structure-preserving randomization inference**: a
conditional randomization test that holds the realized trade structure and the
exogenous price path fixed and re-randomizes only the *placement* of trades on
the calendar, from a known conditional law. Validity is finite-sample exact under
exchangeability of placements. The leading application is entry timing on gold
futures (`GC=F`); the headline is a null — no robust, measure-invariant
entry-placement skill — confirmed on an 11-strategy `GC=F` panel, a 322-test
cross-asset panel under multiplicity control, a measure-family sensitivity range
with an intersection–union reading, and a head-to-head against White's Reality
Check and Hansen's SPA.

The structure-preserving null is implemented in `Code/monte_carlo.py`; the eleven
strategy rules and the verdict classifier are documented in the Supplement
(Section S1).

## Repository layout

| Path | Contents |
|------|----------|
| `Code/` | SPR null, strategy agents/metrics, data loader, validation & figure scripts |
| `Data_Clean/` | Derived data: regime-labeled OHLCV, realized trade logs, per-asset result CSVs (`1d/`, `1h/`, `4h/`) |
| `Charts/` | Figures emitted by the analysis scripts |
| `ProvidedFigures/` | Final numbered manuscript figures |
| `paper.tex`, `supplement.tex` | LaTeX sources (assembled by `Code/build_main.py` / `Code/build_supplement.py`) |
| `paper.pdf`, `supplement.pdf` | Compiled PDFs |

## Installation

Requires **Python 3.11+** (developed and run under 3.14). No compiler or GPU
needed; all dependencies are pure-Python wheels.

```bash
git clone https://github.com/ampatel355/FORTUNAFRAMEWORK.git
cd Fortuna
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

All reproduction commands below assume the virtual environment lives at `.venv/`
and are run from the repository root. They write outputs into `Data_Clean/` and
`Charts/`; the derived inputs they consume are already committed, so **no network
access is required** to reproduce the published numbers.

## Seed protocol

Every Monte Carlo run is deterministic under a documented seed protocol.

- **Single-ticker `GC=F` panel.** Fixed initial seed **42**; independent
  strategy-specific pseudo-random streams are spawned from it. For deterministic
  strategies the realized trade log is fixed across runs and only the null
  simulations vary. The Random baseline regenerates its realized trade sequence
  under each seed (so realized outcome *and* null vary).
- **Seed-robustness (Supplement S5).** 100 outer runs with outer-run seed
  `seed_r = 100 + r`, `r = 1..100`, 5,000 simulations per run.
- **Synthetic worlds.** Base seed **9100**.
- **Competitor comparison.** Fixed world-offset seeds with `PYTHONHASHSEED=0`.
- **Positive control / signals.** One spawned stream per seed; `PC_SEEDS` controls
  the count.

Several scripts re-verify their regenerated statistics against the published
values and **abort on any material mismatch**, so figures and text cannot silently
diverge.

## Reproducing each result

Run from the repository root. Environment variables set the documented run sizes;
smaller values reproduce the same point estimates within Monte Carlo error and run
faster.

### Main paper

| Result | Script | Command (env vars as published) | Output |
|--------|--------|----------------------------------|--------|
| **GC=F 11-strategy panel** (`tab:main`); equity curves, MC panel, RCSI/percentile, regime ratios | `Code/regenerate_gallery.py` | `MONTE_CARLO_REPRODUCIBLE=1 ./.venv/bin/python Code/regenerate_gallery.py` | figures in `Charts/`; verified against published values |
| **Competitor comparison** vs Reality Check & SPA, 5 known-truth worlds (`tab:competitor`, `fig:competitor`) | `Code/competitor_comparison.py` | `CC_REPLICATIONS=400 CC_BOOT=999 CC_SIMULATIONS=2000 PYTHONHASHSEED=0 ./.venv/bin/python Code/competitor_comparison.py` | `Data_Clean/competitor_comparison.csv`, `Charts/competitor_comparison.png` |
| **Schedule-measure sensitivity**, 3 measures (`tab:schedule_sensitivity`) | `Code/schedule_measure_sensitivity.py` | run once per measure (below) | `Data_Clean/GC=F_sensitivity_*.csv` |

Schedule-measure sensitivity — one invocation per column:

```bash
MEASURE_LABEL=baseline \
  ./.venv/bin/python Code/schedule_measure_sensitivity.py
MONTE_CARLO_MIN_LEADING_INDEX=200 MEASURE_LABEL=leading_gap_200 \
  ./.venv/bin/python Code/schedule_measure_sensitivity.py
MONTE_CARLO_CONTEXT_MATCHING=1 MEASURE_LABEL=context_matched \
  ./.venv/bin/python Code/schedule_measure_sensitivity.py
```

The `baseline` column reproduces the main panel exactly, confirming the
sensitivity harness matches the canonical pipeline.

### Online Supplement

| Result | Script | Command | Output |
|--------|--------|---------|--------|
| **S2** synthetic validation (size, power, KS uniformity) | `Code/synthetic_timing_experiments.py` | `SYNTHETIC_REPLICATIONS=1500 SYNTHETIC_POWER_REPLICATIONS=400 SYNTHETIC_SIMULATIONS=2000 ./.venv/bin/python Code/synthetic_timing_experiments.py` | `Data_Clean/synthetic_null_validation_summary.csv`, `Charts/synthetic_type1_calibration.png`, `Charts/synthetic_power_curve.png` |
| **S2** real-path positive control (injected skill α) | `Code/positive_control_power.py` | `PC_SEEDS=100 ./.venv/bin/python Code/positive_control_power.py` | `Data_Clean/GC=F_positive_control_power_summary.csv`, `Charts/positive_control_skill_curve.png` |
| same, stochastic execution costs (robustness) | `Code/positive_control_power.py` | `MONTE_CARLO_SIMULATE_EXECUTION_COSTS=1 PC_SEEDS=20 ./.venv/bin/python Code/positive_control_power.py` | `Data_Clean/GC=F_positive_control_power_costson_summary.csv` |
| **S2** realistic-signal detection | `Code/positive_control_signals.py` | `./.venv/bin/python Code/positive_control_signals.py` | `Charts/positive_control_signal_curve.png` |
| **S3** cross-asset panel, 322 tests, BH & Bonferroni | `Code/cross_asset_multiplicity.py` | `./.venv/bin/python Code/cross_asset_multiplicity.py` | `Data_Clean/cross_asset_panel_summary.csv`, `Charts/cross_asset_multiplicity.png` |
| **S3** alternative-null benchmark (shuffled / stationary-bootstrap returns) | `Code/null_benchmark_comparison.py` | `./.venv/bin/python Code/null_benchmark_comparison.py` | `Charts/null_method_comparison.png` |
| **S3** multi-asset walk-forward panel | `Code/multi_asset_walk_forward.py` | `./.venv/bin/python Code/multi_asset_walk_forward.py` | walk-forward CSVs, `Charts/multi_asset_walk_forward_inference.png` |
| **S3** bounded frequency-robustness (daily / 4h / hourly) | `Code/frequency_robustness_summary.py` | `./.venv/bin/python Code/frequency_robustness_summary.py` | `Charts/frequency_robustness_pvalue_percentile.png` |
| **S4–S6** per-strategy MC summaries, regime heatmap, seed-robustness, figure gallery | `Code/regenerate_gallery.py` | `MONTE_CARLO_REPRODUCIBLE=1 ./.venv/bin/python Code/regenerate_gallery.py` | gallery PNGs in `Charts/`; verified before any figure is written |

Manuscript PDFs are assembled and compiled with a standard `latexmk`/`elsarticle`
toolchain (compile `paper.tex` first, then `supplement.tex`, which references the
main paper via `xr-hyper`):

```bash
./.venv/bin/python Code/build_main.py        # writes paper.tex
./.venv/bin/python Code/build_supplement.py  # writes supplement.tex
latexmk -pdf paper.tex && latexmk -pdf supplement.tex
```

## Data provenance and terms

The underlying price series — gold futures (`GC=F`) and the cross-asset universe
of 47 instruments — were obtained from **Yahoo Finance** through the
[`yfinance`](https://github.com/ranaroussi/yfinance) package. They are
redistributed here **only in derived form** — regime-labeled OHLCV series,
realized trade logs, and per-asset result tables in `Data_Clean/` — which is what
the reproduction commands consume.

Raw vendor feeds are **not** redistributed: they remain subject to Yahoo
Finance's terms of use and to `yfinance`'s usage terms. To re-download raw data,
set the ticker via the `TICKER` environment variable and use the included loader:

```bash
TICKER="GC=F" ./.venv/bin/python Code/data_loader.py
```

## License

Code in this repository is released under the **MIT License** (see `LICENSE`).
The derived data in `Data_Clean/` is provided for the sole purpose of reproducing
the paper's results; redistribution of the underlying market data remains governed
by Yahoo Finance's terms of use.

## Citation

See `CITATION.cff`, or cite the archived release at
https://doi.org/10.5281/zenodo.20695539.
