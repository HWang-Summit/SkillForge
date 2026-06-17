# QA checklist

## Grounding checks

- Every substantive evaluation should be traceable to either:
  - `references/editorial criteria and processes.md`, or
  - manuscript facts extracted from accepted files.
- User chat text was used only for task routing, file-location, or parameter-selection context, not as manuscript evidence.
- For PDF reviews, confirm the assessment considered both parsed text and PDF visual renderings unless one failed and the boundary says so.
- For LaTeX reviews, confirm the assessment considered source files and corresponding PDF visual renderings unless one failed and the boundary says so.
- No reviewer persona detail should appear beyond allowed `emphasis` labels.
- No technical failing should be invented from domain habit alone when the accepted file evidence does not show it.

## Input provenance checks

- Confirm the `Review setup` lists:
  - `Input package`
  - `Files used as evidence`
  - `Parsed text source`
  - `Visual review source`
  - `Assessment boundary`
- Confirm every file listed as evidence is one of the accepted input classes:
  - manuscript PDF
  - MinerU Markdown or resources derived from a manuscript PDF
  - rendered PDF page PNGs or contact sheet
  - LaTeX source package files
  - PDF visuals corresponding to the LaTeX manuscript
- Confirm unsupported pasted abstracts, author notes, conversational summaries, or background claims were excluded from the fact base.
- If MinerU parsing, PDF rendering, LaTeX source reading, or asset discovery failed, confirm the output states the failure and narrows the assessment accordingly.

## Coverage checks

- Confirm all three reviewer reports exist.
- Confirm the three reports differ in `emphasis` only.
- Confirm each reviewer still addresses all core axes, even if briefly.
- Confirm a `Cross-review synthesis` section exists.
- Confirm a `Risk / unsupported claims` section exists.

## Boundary checks

- Confirm the output stays in reviewer-assessment mode, not author-response mode.
- Confirm the output does not claim a final editorial decision.
- Confirm broad-interest judgment is expressed cautiously, because the source assigns that final judgment to editors.

## Non-invention checks

- No invented reviewer identity, specialty, institution, or selection history.
- No invented experiments, controls, analyses, line numbers, citations, prior-work details, or figure-specific content absent from the input.
- No claims imported from user explanation, prior model knowledge, or domain expectations unless the file evidence supports them.
- If evidence is partial, mark `AUTHOR_INPUT_NEEDED` or `Not assessable from accepted file evidence`.

## Consistency checks

- Shared manuscript facts should stay consistent across all three reviewers.
- Divergence across reviewers should reflect weighting differences, not contradictory factual claims.
- Technical failings listed in the synthesis should match issues already raised in at least one individual report.

## Final release rule

- If the skill cannot produce a grounded three-reviewer package without major invention, it should return a bounded draft review with explicit missing-information flags rather than pretending certainty.
- If no accepted manuscript file evidence is available, it should not produce the review; it should request a PDF manuscript or LaTeX source package with the corresponding PDF.
