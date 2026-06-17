"""Assemble the lean main paper.tex (methodology-first, ~35-40pp) from:
  - the original preamble (+ remark theorem),
  - new framework-first front matter,
  - the drafted Introduction/Related-literature, Theory, Validation/Empirical, Discussion,
  - verbatim methodology core blocks and floats from fortuna_full_backup.tex,
  - a condensed conclusion and a brief data/implementation appendix,
  - the shared bibliography.
Supporting material lives in supplement.tex; main->supplement references are literal
("Online Supplement, Section~S2") so the main paper compiles standalone.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "fortuna_full_backup.tex").read_text().splitlines()
DRAFTS = ROOT / "Code" / "drafts"


def blk(a, b):
    return "\n".join(SRC[a - 1:b])


def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f"[build_main] expected substring not found ({label}): {needle[:80]!r}")
    return text


# ---- preamble (+ remark theorem) -------------------------------------------
doc_start = next(i for i, l in enumerate(SRC, 1) if l.strip() == "\\begin{document}")
preamble = blk(1, doc_start - 1)
preamble = require(preamble, "\\newtheorem{definition}{Definition}", "preamble theorems")
preamble = preamble.replace(
    "\\newtheorem{definition}{Definition}",
    "\\newtheorem{definition}{Definition}\n\\newtheorem{remark}{Remark}", 1)

# ---- front matter (framework-first) ----------------------------------------
FRONT = r"""\begin{document}

\begin{frontmatter}

\title{Structure-Preserving Randomization Inference for Decision Timing}

\author{Aryan Patel}

\begin{abstract}
\begingroup
\parindent=0pt
\emergencystretch=3em
A realized return does not identify skill: profit confounds the quality of a
decision sequence, the structural exposure that sequence implies, and the drift
of the path on which it ran. We develop \emph{structure-preserving randomization
inference}, a conditional randomization test that isolates the marginal
contribution of decisions by holding the realized structure and the exogenous
path fixed and re-randomizing only the decision margin from a known conditional
law. The construction is indexed by a family of structure-preserving measures,
and we treat that family as the inferential object: the timing estimand is
point-identified only given a measure, so the data return a \emph{set} of
measure-specific verdicts, and we give a valid intersection--union test for the
stronger, measure-invariant claim. The test is finite-sample exact under
exchangeability of placements, consistent with a minimum detectable edge of order
$N^{-1/2}$ in the decision count, and attains one-sided Gaussian local power
$\beta(h)=\Phi(h-z_{1-\alpha})$ against placement alternatives while carrying
\emph{zero} noncentrality against pure exposure. In controlled worlds this
orthogonality is visible: White's Reality Check and Hansen's SPA reject a
profitable-but-untimed strategy about two-thirds of the time ($0.660$ and
$0.638$) where the structure-preserving test holds its nominal size ($0.050$),
and all four tests have full power against genuine skill.

\par\smallskip\noindent
The leading application is entry-timing skill in trading. On daily gold futures
(GC=F, 2002-03-04 to 2026-04-02; buy-and-hold cumulative return $14.670$), no
strategy in an eleven-rule panel shows entry-placement skill at $p\le0.05$ before
or after Benjamini--Hochberg adjustment; the verdict is robust to a leading-gap
feasibility restriction but reverses under a context-matched measure---exactly
the partial-identification content of the measure family made empirical---so we
report the absence of \emph{robust, measure-invariant} entry-placement skill.
Across $322$ strategy-by-asset tests on $47$ instruments nothing survives
Benjamini--Hochberg or Bonferroni control, with random-entry baselines among the
most extreme. The same recipe---fix the path, preserve the structure, randomize
the decision margin---applies wherever a decision sequence is overlaid on an
exogenous process.
\endgroup
\end{abstract}

\begin{keyword}
Conditional randomization inference \sep Partial identification \sep
Backtesting \sep Trading skill \sep Monte Carlo \sep Data snooping
\end{keyword}

\end{frontmatter}
"""

# ---- Section 3: Methodology (verbatim core + bridge) -----------------------
METH_BRIDGE = r"""\section{Methodology}

A trading strategy maps market information to a sequence of exposure decisions;
its realized return is the product of an exogenous return process and an
endogenous timing process. A backtest reports that product and is often read as
skill, conflating three sources: the quality of entry placement, the structural
exposure the strategy's geometry implies, and the drift of the realized path. We
isolate the first. Conditional on the realized structural profile, the test asks
whether entry placement earns more than a structure-matched random implementation
on the same path.

"""

methodology = (
    METH_BRIDGE
    + blk(117, 121) + "\n\n"      # Definition: structure-preserving null & entry-placement skill
    + blk(165, 178) + "\n\n"      # Formal problem statement (H0/H1)
    + "\\subsection{Data, execution, and trade extraction}\n\n"
    + "The data pipeline (feature construction and forward-safe regime labeling), "
      "the next-bar execution and fill model, and the eleven strategy rules are "
      "specified in the Online Supplement (Section~S1); all strategies share next-bar "
      "execution, non-overlapping positions, and an expected round-trip cost "
      "$c=0.000470$ applied identically to the realized trades and to every simulated "
      "schedule. We retain here only the trade-structure objects the null requires.\n\n"
    + blk(200, 220) + "\n\n"      # trade structure extraction (formulas; skip its \subsection title at 198-199)
    + blk(222, 249) + "\n\n"      # conditioning set and estimand
    + blk(251, 295) + "\n\n"      # SPR + Algorithm + sampling distribution + def:h0
    + blk(347, 372).replace("\\subsection{Schedule-measure sensitivity}",
                            "\\subsection{The measure family}", 1) + "\n\n"  # tab:schedule_measures
    + blk(417, 442)               # RCSI / RCSI_z / p-hat / percentile
)

# ---- Section 1+2: Introduction + Related literature -------------------------
intro = (DRAFTS / "intro.tex").read_text()
intro = require(intro, "(Sections~\\ref{sec:simulation-validation} and \\ref{sec:positive-control})",
                "intro pc-ref")
intro = intro.replace("(Sections~\\ref{sec:simulation-validation} and \\ref{sec:positive-control})",
                      "(Section~\\ref{sec:simulation-validation})")

# ---- Section 4: Theory ------------------------------------------------------
theory = (DRAFTS / "theory.tex").read_text()
# strip the leading %-comment banner lines (keep from the \section onward)
theory = theory[theory.index("\\section{Theoretical properties}"):]
theory = theory.replace("Section~\\ref{sec:positive-control}", "Section~\\ref{sec:simulation-validation}")
# drop the trailing editor note comment block
if "% NOTE TO EDITOR" in theory:
    theory = theory[:theory.index("% NOTE TO EDITOR")].rstrip() + "\n"

# ---- Section 5+6: Validation + Empirical (literal supplement refs) ----------
cond = (DRAFTS / "condense.tex").read_text()
# drop trailing comment block
if "% ---------------------------------------------------------------------------" in cond:
    cond = cond[:cond.index("% ---------------------------------------------------------------------------")].rstrip() + "\n"

repls = [
    ("(Section~\\ref{sec:supp-synthetic}), the realistic-signal mechanisms (Section~\\ref{sec:supp-signals}), and the full calibration and power figures (Section~\\ref{sec:supp-calibration-figs}).",
     "(Online Supplement, Section~S2)."),
    ("Construction details are in Section~\\ref{sec:supp-synthetic}.",
     "Construction details are in the Online Supplement (Section~S2)."),
    ("(Section~\\ref{sec:supp-calibration-figs})", "(Online Supplement, Section~S2)"),
    ("(Section~\\ref{sec:supp-positive-control})", "(Online Supplement, Section~S2)"),
    ("(Section~\\ref{sec:supp-signals})", "(Online Supplement, Section~S2)"),
    ("(Sections~\\ref{sec:supp-mc-summaries}--\\ref{sec:supp-seed-robustness})",
     "(Online Supplement, Sections~S3 and~S5)"),
    ("detailed in Section~\\ref{sec:supp-cross-asset}, alongside the exploratory multi-asset walk-forward panel (Section~\\ref{sec:supp-walk-forward}) and the bounded daily/4-hour/hourly frequency check (Section~\\ref{sec:supp-frequency}),",
     "detailed in the Online Supplement (Section~S3), alongside the exploratory multi-asset walk-forward panel and the bounded daily/4-hour/hourly frequency check (both in Section~S3),"),
    # keep tab:schedule_sensitivity IN the main paper: insert it and rewrite the pointer
    ("The full sensitivity table and the leading-gap column are in Section~\\ref{sec:supp-schedule-sensitivity}.",
     "Table~\\ref{tab:schedule_sensitivity} reports the full panel under all three measures.\n\n"
     + blk(732, 761)),
    # tab:main notes: avoid implying in-main figures
    ("the final cumulative returns shown in the equity-curve figure for the common window 2002-03-04 to 2026-04-02.",
     "the final cumulative returns for the common window 2002-03-04 to 2026-04-02 (equity curves in Online Supplement~S6)."),
    ("RCSI is reported as mean $\\pm$ SD across outer-run seeds from the robustness figure (outer runs = 100, simulations per run = 5{,}000, transaction cost = 0.000470).",
     "RCSI is reported as mean $\\pm$ SD across outer-run seeds (outer runs = 100, simulations per run = 5{,}000, transaction cost = 0.000470; Online Supplement~S5)."),
]
for old, new in repls:
    cond = require(cond, old, "condense repl")
    cond = cond.replace(old, new, 1)

# ---- Section 7: Discussion --------------------------------------------------
discussion = (DRAFTS / "measure.tex").read_text()

# ---- Section 8: Conclusion (condensed, framework-first) ---------------------
CONCLUSION = r"""\section{Conclusion}

The relevant object of inference in evaluating a decision sequence is not its
realized payoff but the contribution of the decisions relative to a counterfactual
that carries the same structural burden on the same path. Structure-preserving
randomization inference supplies that counterfactual as a finite-sample-exact
conditional test, makes the conditioning measure an explicit part of the
identification statement, and---because the measure is a choice---identifies a set
of measure-specific verdicts rather than a single number, with measure invariance
the strongest claim the design supports.

Applied to daily gold futures, the framework finds profit common but
robust, measure-invariant entry-placement skill absent: no strategy clears
$p\le0.05$ under the neutral measure, the verdict reverses under a context-matched
measure, and across $322$ strategy-by-asset tests on $47$ instruments nothing
survives multiplicity control. Synthetic worlds and a real-path positive control
confirm the test is correctly sized and powered, and the head-to-head comparison
shows where return-based tests mistake structural exposure for skill. The reading
is not that the strategies are bad but that, within the scope of the timing test,
realized profitability is not separately identifiable from structural exposure.

The construction is general. Wherever a decision sequence is overlaid on an
exogenous process---factor and allocation timing, execution scheduling, the
evaluation of learned policies, the timing of forecasts---the same recipe holds
the structural footprint fixed, randomizes the decision margin, and refers the
realized statistic to the law this induces. The validity, local-power, and
partial-identification results transfer, and the measure family returns as the
object to specify.
"""

# ---- Appendix A: data & implementation summary ------------------------------
APPENDIX = r"""\appendix

\section{Data and implementation}
\label{app:data}

The primary analysis uses daily gold futures (GC=F) over 2002-03-04 to 2026-04-02;
the buy-and-hold cumulative return over the window is $14.670$. All strategies and
their Monte Carlo null paths share an expected round-trip transaction cost of
$c=0.000470$ in return units, calibrated to daily execution and held fixed at higher
frequencies. The panel comprises eleven rules---Trend Pullback, Breakout Vol+Mom,
Mean Rev Vol Filter, Validation AVM, ADX Trend, Oversold Reversion, Squeeze
Breakout, Connors RSI2, Donchian Reentry, Turn-of-Month, and a Random control---with
thresholds fixed before the reported run and applied identically across assets. The
data pipeline, forward-safe regime labeling, next-bar execution and fill model,
strategy rule definitions, the verdict classifier, the Monte Carlo and seed-robustness
protocols, and the full reproduction commands are in the Online Supplement
(Sections~S1 and~S7); code and derived data are archived at
\url{https://github.com/ampatel355/Fortuna} and \url{https://doi.org/10.5281/zenodo.20724999}.
"""

bib = blk(1197, len(SRC))  # \bibliographystyle ... thebibliography ... \end{document}

out = "\n".join([
    preamble, FRONT,
    intro, "",
    methodology, "",
    theory, "",
    cond, "",
    discussion, "",
    CONCLUSION, "",
    APPENDIX, "",
    bib, "",
])
(ROOT / "paper.tex").write_text(out)
print(f"wrote paper.tex ({len(out.splitlines())} lines)")
print("sections:", out.count("\\section{"))
print("end{document}:", out.count("\\end{document}"))
