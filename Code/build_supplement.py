"""Assemble supplement.tex from byte-exact blocks of fortuna_full_backup.tex.

Moves all supporting material (implementation, synthetic worlds, positive control,
realistic signals, alternative-null comparison, multi-asset, frequency robustness,
per-strategy MC, regime analysis, seed robustness, figure gallery, reproducibility)
into an online Supplementary Appendix. Verbatim extraction preserves every number;
xr-hyper lets the supplement reference the main paper's labels.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "fortuna_full_backup.tex").read_text().splitlines()


def blk(a, b):
    """1-indexed inclusive line range, byte-exact."""
    return "\n".join(SRC[a - 1:b])


def demote(text):
    """Demote a leading \\section to \\subsection (for moved appendices)."""
    return text.replace("\\section{", "\\subsection{", 1)


# locate end of preamble
doc_start = next(i for i, l in enumerate(SRC, 1) if l.strip() == "\\begin{document}")
preamble = blk(1, doc_start - 1)
bib = blk(1197, len(SRC))  # \bibliographystyle + thebibliography

SUPP_PREAMBLE = preamble + r"""

% --- supplement-specific ---
\usepackage{xr-hyper}
\externaldocument{paper}              % resolve \ref to the main paper's labels
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\thesubsection}{S\arabic{section}.\arabic{subsection}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\renewcommand{\theproposition}{S\arabic{proposition}}
"""

HEAD = SUPP_PREAMBLE + r"""
\begin{document}

\begin{frontmatter}
\title{Supplementary Appendix to\\ ``Structure-Preserving Randomization for Backtest Timing Inference''}
\author{Aryan Patel}
\begin{abstract}
\noindent This appendix collects the implementation details, the full validation
suite, the additional empirical analyses, and the reproducibility material that
support the main paper. Section and equation references of the form ``Section~4''
or ``Proposition~1'' point to the main paper; references prefixed ``S'' are internal
to this appendix. Every reported quantity is the direct output of the accompanying
code on the canonical data; the reproduction commands are listed in
Section~\ref{supp:repro}.
\end{abstract}
\end{frontmatter}

\setcounter{section}{0}
"""

sections = []

# S1 Implementation details
sections.append(
    "\\section{Implementation details}\n\\label{supp:implementation}\n\n"
    "This section specifies the data pipeline, trade generation, Monte Carlo and "
    "robustness machinery, the execution and fill model, and the strategy rule set "
    "summarized in the main paper.\n\n"
    + blk(180, 186) + "\n\n"          # data preparation
    + blk(188, 196) + "\n\n"          # trade generation
    + blk(374, 401) + "\n\n"          # Monte Carlo simulation
    + blk(403, 415) + "\n\n"          # robustness design
    + "\\subsection{Verdict classifier}\n\n" + blk(444, 444) + "\n\n"  # classifier paragraph
    + demote(blk(1110, 1113)) + "\n\n"   # execution and fill model (\section->\subsection)
    + demote(blk(1115, 1141))            # strategy rule definitions (\section->\subsection)
)

# S2 Validation in known-truth environments (synthetic + positive control + realistic signals)
# Rename the moved \section/\label so it does not collide with the main paper's
# kept \label{sec:simulation-validation}.
sections.append(
    "\\section{Validation in known-truth environments}\n\\label{sec:supp-synthetic}\n"
    + blk(452, 590)                    # body after the original \section + \label lines
)

# S3 Additional empirical analyses (cross-asset, alt nulls, multi-asset, frequency, anatomy, per-strategy MC)
crossasset = blk(817, 860).replace("\\label{sec:cross-asset-multiplicity}",
                                   "\\label{sec:supp-cross-asset}", 1)
sections.append(
    "\\section{Additional empirical analyses}\n\\label{supp:additional}\n\n"
    + crossasset + "\n\n"              # cross-asset breadth + multiplicity (moved from main)
    + blk(687, 725) + "\n\n"          # comparison to alternative nulls
    + blk(767, 815) + "\n\n"          # multi-asset walk-forward
    + blk(862, 899) + "\n\n"          # frequency robustness
    + blk(907, 909) + "\n\n"          # anatomy of weak skill
    + blk(911, 951)                    # per-strategy MC distribution summaries
)

# S4 market regime analysis
sections.append(blk(953, 990))
# S5 seed robustness
sections.append(blk(992, 1004))
# S6 figure gallery
sections.append(blk(1007, 1060))
# S7 reproducibility (relabel for xr target)
sections.append(blk(1143, 1195).replace("\\section{Reproducibility appendix}",
                                         "\\section{Reproducibility}\n\\label{supp:repro}", 1))

body = "\n\n".join(sections)
out = HEAD + "\n" + body + "\n\n" + bib + "\n"   # bib block already ends with \end{document}
(ROOT / "supplement.tex").write_text(out)

# verification: print first/last line of each extracted block
print("=== boundary check ===")
checks = [("data prep", 180, 186), ("trade gen", 188, 196), ("MC sim", 374, 401),
          ("robustness", 403, 415), ("classifier", 444, 444), ("execution", 1110, 1113),
          ("strategy rules", 1115, 1141), ("validation S2", 450, 590),
          ("alt nulls", 687, 725), ("multi-asset", 767, 815), ("frequency", 862, 899),
          ("anatomy", 907, 909), ("per-strat MC", 911, 951), ("regime", 953, 990),
          ("seed robust", 992, 1004), ("figures", 1007, 1060), ("repro", 1143, 1195),
          ("bib", 1197, len(SRC))]
for name, a, b in checks:
    print(f"[{name:14s} {a}-{b}]  FIRST: {SRC[a-1][:70]!r}")
    print(f"{'':22s}  LAST : {SRC[b-1][:70]!r}")
print(f"\nwrote supplement.tex ({len(out.splitlines())} lines)")
