# Cover Letter — submission to *Risks* (MDPI)

Dear Editor-in-Chief,

I am pleased to submit the enclosed manuscript, **"Structure-Preserving Randomization Inference for Decision Timing,"** for consideration in *Risks*. The work is original, has not been published previously, and is not under review at any other journal. I am the sole author. There are no competing interests to declare, and the research received no external funding.

The paper sits squarely within the journal's remit of quantitative inference and risk methodology. Its central object is the choice of conditioning measure that defines a test, which the paper treats explicitly as a source of model risk rather than concealing in a single specification. The associated uncertainty is quantified directly: instead of returning one verdict, the framework reports a sensitivity range of measure-specific verdicts over a declared admissible menu and supplies a valid test for the stronger, measure-invariant claim. The method is Monte Carlo in implementation and is delivered with full reproducibility. Entry-timing in trading is the leading application and the testbed throughout, but it is the vehicle for the methodology, not the point of the paper.

Methodologically, the contribution is a finite-sample valid conditional randomization test that isolates the marginal contribution of a decision sequence by holding the realized structure and the exogenous path fixed and re-randomizing only the decision margin from a chosen conditional law. Because the verdict is point-identified only given a measure, the measure family is made part of the inferential object through a partial-identification treatment, with an intersection-union test for the measure-invariant claim whose power is governed by the least-favorable admissible measure. The test's orthogonality to structural exposure is demonstrated head-to-head against return-based procedures: on known-truth worlds, White's Reality Check and Hansen's SPA reject a profitable-but-untimed strategy roughly two-thirds of the time (0.660 and 0.638) where the structure-preserving test holds its nominal size, while all procedures retain full power against genuine skill. Applied to daily gold futures and to a 322-test, 47-instrument cross-asset panel, the analysis finds no robust, measure-invariant timing skill, a deliberately falsificationist null.

All code and derived data are publicly archived on GitHub (https://github.com/ampatel355/FORTUNAFRAMEWORK) and on Zenodo (DOI 10.5281/zenodo.20724999). The pipeline uses deterministic seeds, and a full supplement documents the constructions, proofs, and replication artifacts, so every reported figure and table can be regenerated end to end.

I confirm that neither the manuscript nor any parts of its content are currently under consideration for publication with, or published in, another journal. As the sole author, I have approved the manuscript and agree with its submission to Risks, and I declare no conflicts of interest. Given the emphasis on model risk, uncertainty quantification, and Monte Carlo inference, I believe the paper would be well served by an Associate Editor in statistical or computational risk methodology, and I am happy to suggest reviewers on request.

In the interest of full transparency, I disclose that the generative AI assistant Claude (Anthropic) was used during preparation to help write portions of the analysis code and to review and refine the writing; I reviewed and edited all such output and take full responsibility for the content.

Thank you for your consideration.

Sincerely,
Aryan Patel
