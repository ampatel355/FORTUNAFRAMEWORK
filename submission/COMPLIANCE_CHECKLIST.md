> **STATUS (final pre-submission build, 2026-06-16).** The MDPI port is COMPLETE. The
> submission artifact is `paper_mdpi.tex` / `paper_mdpi.pdf` (class
> `\documentclass[risks,article,submit]{Definitions/mdpi}`), with all MDPI front/back-matter
> macros, JEL/MSC codes, Chicago author-date references via `\bibliography{fortuna}`, ORCID
> `0009-0008-2097-6170`, and a 199-word single-paragraph abstract. The checklist below is the
> ORIGINAL pre-port plan (written against the `elsarticle` `paper.tex`); every item marked
> "convert to MDPI" is now satisfied by that build. Remaining genuine author actions:
> (1) confirm the Zenodo record metadata matches the paper and re-archive the cleaned repo;
> (2) supply suggested-reviewer institutional emails; (3) decide and add a generative-AI use
> disclosure; (4) confirm the current APC rate; (5) upload via the submission portal.

## A. Template & document class
- [ ] ⚠️ **Convert to official MDPI class.** Manuscript is currently `\documentclass[preprint,12pt]{elsarticle}` (Elsevier). MDPI requires the **`mdpi.cls`** LaTeX template (or the MDPI Word template). This is the single largest pre-submission task — most items below depend on it.
- [ ] ⚠️ **Add MDPI front-matter fields.** `\Title`, `\Author`, `\address`, `\corres`, `\firstnote`, plus journal/volume metadata supplied by the class are not present (elsarticle uses `\title`/`\author` only).

## B. Manuscript structure
- [x] ✅ **Abstract** present (single paragraph, ~200 words). MDPI limit is 200 words — current abstract runs slightly long across two paragraphs; ⚠️ tighten to ≤200 words and a single paragraph.
- [x] ✅ **Keywords (3–10).** Eight present in `\begin{keyword}`: conditional randomization inference; model risk; uncertainty quantification; Monte Carlo methods; partial identification; backtesting; data snooping; reproducibility. ⚠️ Move into MDPI `\keyword{}` field on conversion.
- [x] ✅ **Introduction** (§1).
- [x] ✅ **Body sections** present: Related literature (§2), Methodology (§3), Theoretical properties (§4), Validation (§5), Empirical results (§6), Discussion (§7).
- [x] ✅ **Conclusion** (§8) present. ⚠️ MDPI prefers heading "Conclusions" (plural).
- [x] ✅ **Appendices** present (Proofs; Data and implementation). ⚠️ MDPI numbers these `Appendix A`, `Appendix B`; relabel on conversion.

## C. MDPI back matter (all present in text; relabel to MDPI macros on conversion)
- [x] ✅ **Author Contributions w/ CRediT** — full CRediT taxonomy, all "A.P." ("Conceptualization, A.P.; methodology, A.P.; …"). Correct for single author.
- [x] ✅ **Funding** — "This research received no external funding." (MDPI-required wording.)
- [x] ✅ **Institutional Review Board Statement** — "Not applicable."
- [x] ✅ **Informed Consent Statement** — "Not applicable."
- [x] ✅ **Data Availability Statement** — present; cites GitHub repo + Zenodo DOI, derived-data redistribution, deterministic seeds.
- [x] ✅ **Acknowledgments** — present. ⚠️ MDPI section heading is **"Acknowledgments"** (US spelling) — current spelling already matches; keep as-is.
- [x] ✅ **Conflicts of Interest** — "The author declares no conflict of interest."
- [ ] ⚠️ **Use MDPI back-matter macros** (`\authorcontributions`, `\funding`, `\institutionalreview`, `\informedconsent`, `\dataavailability`, `\acknowledgments`, `\conflictsofinterest`) instead of the current bold-run-in `\noindent\textbf{...}` formatting.

## D. Supplementary Materials
- [x] ✅ Supplement exists (`supplement.tex`) and is cited throughout the body (e.g., §3, §5, §6).
- [ ] ⚠️ **Rename the citation to "Supplementary Materials."** Body currently calls it "Online Supplement" / "online Supplementary Material" / "Online Supplement, Section S2". MDPI requires a dedicated **"Supplementary Materials"** back-matter statement and references in the form "Figure S1, Table S1." Add the statement (e.g., "The following supporting information can be downloaded at: …").

## E. References
- [ ] ⚠️ **Reformat to MDPI/ACS style.** Bibliography is a hand-built `\begin{thebibliography}` under `\bibliographystyle{elsarticle-num}`. MDPI *Risks* uses its own numbered style (`mdpi.bst` / `\bibliography{...}` with the MDPI template, or Chicago author–date per journal setting). 35 entries present and internally consistent.
- [ ] ⚠️ **Add DOIs to references** where available — MDPI strongly encourages a DOI on every reference.
- [ ] ◻️ Verify all in-text `\cite` keys resolve and that every reference is cited (no orphan entries).

## F. Figures & tables
- [x] ✅ Figures are raster **PNG** (`Charts/` 119 PNG, `ProvidedFigures/` 19 PNG); one figure embedded in `paper.tex` (`competitor_comparison.png`), the rest in the supplement.
- [ ] ⚠️ **Resolution check.** MDPI requires ≥1000 dpi for line art / ≥300 dpi for photos, or vector (PDF/EPS) preferred. Confirm each PNG meets dpi; regenerate as vector PDF from the plotting code where possible.
- [x] ✅ **Captions present** (6 `\caption{}` in paper; all supplement figures captioned). ⚠️ MDPI caption format: "**Figure 1.** …" / "**Table 1.** …" with bold label and terminal period.
- [ ] ◻️ Ensure every figure/table is cited in text before it appears and uploaded as separate high-res files at submission.

## G. Reproducibility (code + data + DOI)
- [x] ✅ **Code** archived: GitHub `https://github.com/ampatel355/FORTUNAFRAMEWORK` (`Code/`, `Data_Clean/`, `requirements.txt`).
- [x] ✅ **Data** redistributed in derived form with re-download path via `yfinance` loader; deterministic seed protocol stated.
- [x] ✅ **Persistent DOI**: Zenodo `10.5281/zenodo.20724999`, cited in Data Availability + Appendix.
- [ ] ◻️ Confirm the Zenodo archive is **public and the version matches the submitted manuscript** (tag the exact commit).

## H. Author identifiers & submission portal items
- [ ] ⚠️ **ORCID** — no ORCID iD in the source. Register/obtain one and add to the MDPI author profile and `\orcidA{}` field; MDPI displays it on the article.
- [ ] ⚠️ **Suggested reviewers** — supply 3–5 suggested reviewers (name, affiliation, email, no conflicts) in the submission system; not part of the manuscript file.
- [ ] ◻️ **Cover letter** — prepare a brief cover letter stating novelty, fit to *Risks* (model-risk / uncertainty-quantification framing), and that the work is original and not under review elsewhere.
- [ ] ◻️ Confirm corresponding-author email and affiliation are entered in the portal.

## I. Ethics statements
- [x] ✅ **Human subjects** — N/A; IRB statement "Not applicable." Correct (financial time-series data only).
- [x] ✅ **Animal subjects** — N/A; not applicable to this study. MDPI does not require an animal-ethics statement when none were used; no action needed.

## J. Language & review aids
- [ ] ◻️ **English quality** — single-author, advanced academic English; reads cleanly. Consider a final proofread / MDPI English editing service note; no blocking issue.
- [ ] ⚠️ **Line numbering for review.** Not enabled (no `lineno`/`\linenumbers`; elsarticle's `review` option not set). The MDPI template enables continuous line numbers by default — converting to `mdpi.cls` satisfies this automatically; otherwise add `\usepackage{lineno}\linenumbers`.

## K. Policy, licensing & cost
- [ ] ◻️ **Preprint policy** — MDPI permits prior posting on preprint servers (**SSRN allowed**). If an SSRN/working-paper version exists, disclose it in the cover letter and cite it; no conflict with submission.
- [ ] ◻️ **Licensing (CC BY 4.0)** — MDPI publishes open access under **CC BY 4.0**; author retains copyright. Acknowledge at acceptance (license-to-publish form). No manuscript change needed now.
- [ ] ⚠️ **APC awareness** — *Risks* is open access with an **Article Processing Charge** (currently CHF ~1600; confirm the live rate and any discount/waiver eligibility on the *Risks* journal page before submitting, given no external funding).

---

### Top author-action items before clicking "Submit"
1. ⚠️ Port the manuscript body into **`mdpi.cls`** (drives template, line numbers, back-matter macros, bibliography style).
2. ⚠️ Obtain and add **ORCID**.
3. ⚠️ Rename all supplement references to **"Supplementary Materials"** and add the back-matter statement.
4. ⚠️ Reformat **references** to MDPI style and add DOIs.
5. ⚠️ Prepare **suggested reviewers**, cover letter, and confirm **APC** rate / Zenodo version match.

**Relevant file paths:** `/Users/aryanpatel/Desktop/Fortuna/paper.tex` · `/Users/aryanpatel/Desktop/Fortuna/supplement.tex` · `/Users/aryanpatel/Desktop/Fortuna/paper_refs.bib` · `/Users/aryanpatel/Desktop/Fortuna/Charts/` · `/Users/aryanpatel/Desktop/Fortuna/ProvidedFigures/` · `/Users/aryanpatel/Desktop/Fortuna/README.md`