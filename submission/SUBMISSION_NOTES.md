# Submission notes — *Risks* (MDPI)

## What was done in the Risks revision round

A five-referee Risks panel (favorable, skeptical, quant-finance, hostile
econometrician, statistics professor) plus an editor synthesis was run against the
manuscript. Verdict: **major revision, accept-track** (no reject). All blockers and
majors were resolved:

- **Orthogonality proposition (B1, the load-bearing fix).** The previous proof used a
  false additive decomposition (`log(1+CR)=A(path)+B(placement)` with `A` invariant
  across the resampling orbit and "noncentrality exactly 0"). A template placed at a
  different calendar location earns a different return, so no placement-invariant
  additive component exists. Rewritten as an exact exchangeability argument: a
  *pure-exposure* alternative is one that leaves the conditional placement law
  unchanged, so by Proposition 1 the test holds its level (noncentrality zero), while
  a return-mean test loads on the shifted mean. Result preserved; proof now correct.
- **Definition 7 (B2).** The measure-invariant null was symbol-`∩` ("for every θ") but
  glossed and proved as a union ("some θ"). Corrected to the union
  `H₀^∪ = ⋃_θ H₀^θ`, consistent with the intersection–union (max-p) test.
- **Assumption 1 (M1).** The Hoeffding (1951) attribution was demoted from "exactly the
  content of" to motivating analogy (the ξ_j are functions of the permutation, not a
  fixed array); stated as a genuine high-level CLT condition.
- **IUT power corollary (M5).** Equality `β=Φ(min h_θ − z)` weakened to an inequality
  (with comonotone-limit equality); the spurious "contiguity derived from boundedness"
  step replaced by a one-line Slutsky argument.
- **Cost / roll honesty (M2/M3).** The "costs cancel to first order" claim was downgraded
  to an honest statement (approximate cancellation; omitted frictions bias *toward*
  non-rejection, so the verdict is conservative); the `14.670` buy-and-hold figure now
  carries a units gloss (a gross ≈15.7× multiple, cost-free, roll-inclusive).
- **Model-risk framing made load-bearing (M4, the Risks-fit gate).** The least-favorable-measure
  intersection–union construction is now tied to the robust-risk literature
  (Artzner–Delbaen–Eber–Heath 1999; Hansen–Sargent 2008; Cont 2006), and the language is
  honestly down-scoped to the operative three-measure menu (`Θ₀` enumerated; richer
  sampling left to future work).
- **Squeeze Breakout N=4 (M7), abstract (m1/m9), keywords (m8).** N=4 caveat added at first
  mention; abstract reduced to a single ~205-word paragraph with no false precision;
  keyword "partial identification" → "sensitivity analysis"; JEL (C12, C15, C58, G14) and
  MSC 2020 (62F03, 62G09, 91G70) classification codes added.

Both documents compile clean (0 undefined references, 0 overfull boxes); every retained
numeric value traces to a committed data artifact (faithfulness audit passes).

## Residual author actions before upload (cannot be completed offline here)

1. **Port to the official MDPI `mdpi.cls` template.** The manuscript currently compiles in
   `elsarticle`; the content is MDPI-shaped (single-paragraph ≤~200-word abstract,
   keywords, JEL/MSC, full back matter, Supplementary Materials statement), but MDPI
   requires its own class + `mdpi.bst`. Paste the body into the downloaded `Risks` template
   and switch the bibliography style. (Mechanical; no content change.)
2. **Author metadata.** Add affiliation, corresponding-author email, and ORCID iD on the
   title page (MDPI mandatory).
3. **Suggested reviewers / cover-letter handling note** in the submission system.
4. **Repository hygiene.** The git remote is `…/VF-RCSI.git`; rename to `…/Fortuna` (or
   `git remote set-url`) so it matches the Data Availability Statement and the Zenodo
   archive. Add `LICENSE`, `CITATION.cff`, corrected `requirements.txt`, and `.gitignore`
   (all generated in the repo root) and confirm the Zenodo DOI resolves and the repo is
   public at submission. Pin the `yfinance` snapshot date in the README.
5. **Supplement (optional).** It is self-contained (own title/abstract/bibliography), which
   is acceptable as an uploaded Supplementary PDF; if the production editor prefers, drop
   its standalone abstract and cite the main reference list.

## Deliverables in this folder

- `COVER_LETTER.md` (Document C) — cover letter to the Risks Editor-in-Chief.
- `STATEMENTS.md` (Documents D–G) — Author Contributions (CRediT), Funding, Data
  Availability, Conflicts of Interest, plus IRB/Consent/Supplementary-Materials.
- `REPO_PACKAGE.md` (Document H) — repository structure, README, requirements, CITATION.cff.
- `COMPLIANCE_CHECKLIST.md` (Document I) — MDPI/Risks submission checklist.
- `README_previous_backup.md` — the prior repo README (superseded by the root `README.md`).

## UPDATE — manuscript ported into the genuine MDPI/Risks template

The author supplied the official MDPI template (`Definitions/mdpi.cls`, `mdpi_chicago.bst`,
etc.), so the `mdpi.cls` port that was previously listed as the one un-completable
author-action is now **done**:

- **Citation style corrected.** The downloaded variant was `MDPI_template_APA`, but
  `mdpi.cls` routes the `risks` journal to **Chicago author-date** (`mdpi_chicago.bst`),
  and the Risks author instructions list Risks among the `\citep` author-date journals.
  The manuscript now uses `\documentclass[risks,article,submit,pdftex,oneauthor]{Definitions/mdpi}`
  and Chicago author-date citations — e.g. "(White 2000)", "(Sullivan et al. 1999)".
- **Built files:** `paper_mdpi.tex` (the MDPI source, generated by `Code/build_mdpi.py`
  from `paper.tex`), `fortuna.bib` (34 BibTeX entries, faithfulness-preserved), and the
  compiled **`paper_mdpi.pdf`** (25 pp in MDPI's compact single-column layout).
- **Compile:** `pdflatex paper_mdpi` → `bibtex paper_mdpi` → `pdflatex paper_mdpi` ×2,
  run from the repo root (the `Definitions/` folder must sit beside the `.tex`). Result:
  0 undefined references, 1 negligible 2.7pt overfull box, all 34 references resolved in
  Chicago author-date, all MDPI front/back matter (Title, Author, Abstract, Keywords,
  MSC, JEL, Author Contributions, Funding, IRB, Informed Consent, Data Availability,
  Acknowledgments, Conflicts, Supplementary Materials) present.
- **Faithfulness:** the body is the same prose/tables as `paper.tex`; only theorem
  environment names (lowercase → MDPI Capitalized) and `\cite`→`\citep` were changed.
  Every prose number still traces to a committed artifact.

**Remaining author-actions** (unchanged, now the only ones): fill the title-page
**affiliation, corresponding-author e-mail, and ORCID** (currently bracketed
placeholders), add **suggested reviewers** in the submission system, rename the GitHub
remote `VF-RCSI` → `Fortuna`, and (optional) port the supplement using the MDPI
`supfile` document type. The supplement otherwise uploads as-is.

## UPDATE — rigor-elevation round (theorem expansion + measure-family rebuild)

A second adversarial program ("elevate to a strong methods paper") was run: a
9-dimension audit + theorem-draft + adversarial-verify workflow, integration, then a
fresh 5-lens hostile-referee gate. Vetted package and reviews are in `revision/`
(`REVISION_PLAN.md`, `integration_map.md`, `POST_INTEGRATION_REVIEW.md`, the drafted
`.tex` blocks, and `audit/`). Net changes to `paper.tex`:

- **Theorems.** Four propositions promoted to **Theorems** on a shared counter
  (validity, consistency, orthogonality, intersection–union); local power honestly
  **demoted to a Corollary** of consistency. `build_mdpi.py` `transform()` updated to
  capitalize `theorem`/`lemma` for the MDPI class.
- **Assumptions.** Consolidated **Standing Assumptions** block (A1–A12, contiguous) at
  the end of Methodology; `ass:clt` gained an **alternative-law clause** that closes a
  real circularity gap (the consistency/local-power proofs need normality of the
  *centered* statistic under the alternative).
- **Measure family rebuilt.** Admissibility predicate (AM1–AM3), `lem:admissible-validity`,
  conditioning partial order (`prop:lattice`, gap-permutation is the minimum),
  sensitivity region, and `prop:minimax` (least-favorable structure; the power ceiling is
  stated strictly as an **upper bound**, not maximin-optimal). `rem:id-vs-manski`:
  the range is the image of the estimand map, **not** a sharp Manski identified set.
- **Limitations & failure modes** subsection added (R1–R4 repairs, L1–L8 honest
  acknowledgements); "lower bound on total strategy skill" **retracted** and the
  *powered single-measure* result foregrounded over the low-power invariant verdict.
- **Overclaims stripped** ("general apparatus/framework", "identification tool",
  "finite-sample-exact"→"finite-sample valid", "where return-based tests fail"→"answer a
  different question") across main + supplement; register pulled toward Lehmann–Romano.
- **8 verified references added** (Manski 2003, Tamer 2010, Gilboa–Schmeidler 1989,
  Rosenbaum 2002, Imbens–Rubin 2015, Vovk 2005, Lei 2018, Walley 1991) to both the inline
  bibliography and `fortuna.bib`.

**Faithfulness:** value-level numeric diff vs the pre-round snapshot is empty (no
empirical figure changed, removed, or fabricated). All three documents compile clean
(`paper` 56 pp, `paper_mdpi` 36 pp, `supplement` 37 pp; 0 undefined refs, 0
multiply-defined labels). Abstract trimmed to ~229 words.

**Open items requiring execution (NOT run; never fabricated), flagged in the paper as
future work:** (1) a regime/block-preserving measure on the GC=F panel to arbitrate the
four context-matched rejections (highest value; likely needs new code); (2) exact
enumerated p-values for the N=4 Squeeze Breakout orbit; (3) distinct-schedule /
null-dispersion diagnostics across the 322-test panel; (4) duration-permutation and
joint (h,g)-pairing measures to widen the sensitivity range; (5) a verified combinatorial
CLT theorem matched to the mixing permutation statistic (Hoeffding stays an analogy).
