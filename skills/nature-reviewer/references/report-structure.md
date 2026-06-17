# Report structure

## Default output contract

- The default output should contain these sections in order:
  1. `Review setup`
  2. `Reviewer 1`
  3. `Reviewer 2`
  4. `Reviewer 3`
  5. `Cross-review synthesis`
  6. `Risk / unsupported claims`

## Review setup

- Include:
  - `Input package`
  - `Files used as evidence`
  - `Parsed text source`
  - `Visual review source`
  - `Assessment boundary`
  - `Shared manuscript claim summary`
  - `Visible evidence base`
  - `Missing materials affecting confidence`, when applicable
- `Files used as evidence` must list only accepted file-derived inputs, not chat summaries or author explanations.
- `Parsed text source` should name the MinerU Markdown output for PDF workflows or the LaTeX source files used for LaTeX workflows.
- `Visual review source` should name the contact sheet and any single-page PNGs inspected, or state `Not available` with the reason.

## Per-reviewer structure

- Each reviewer report should use the same skeleton:
  - `Overall assessment`
  - `Who would be interested in the results, and why`
  - `Major strengths`
  - `Major concerns`
  - `Technical failings that need to be addressed before the case is established`
  - `Assessment against Nature-style criteria`
  - `Recommendation posture`
- `Assessment against Nature-style criteria` should explicitly touch:
  - `originality`
  - `scientific importance`
  - `interdisciplinary readership`
  - `technical soundness`
  - `readability for nonspecialists`
- `Recommendation posture` should stay reviewer-like, for example:
  - `supportive if technical concerns are resolved`
  - `promising but broad-interest case remains underdeveloped`
  - `currently not established from the accepted file evidence`

## Cross-review synthesis structure

- Include:
  - `Consensus strengths`
  - `Consensus technical risks`
  - `Where emphasis differs across reviewers`
  - `Broad-interest / significance readout`
  - `Most important issues to resolve before a strong Nature-style case is established`

## Risk / unsupported claims section

- Include explicit flags for:
  - unsupported novelty claims
  - significance claims not established by the accepted file evidence
  - missing controls, validations, or comparisons
  - readability claims that cannot be assessed from the accepted file evidence
  - any place where the review necessarily relied on partial file evidence
  - any file parsing, rendering, or source-package gaps that constrain confidence
  - any user-supplied chat claims that were excluded because they were not present in accepted file evidence

## Style rules

- Keep tone formal, direct, and evidence-based.
- Do not write as the authors.
- Do not write a rebuttal, action plan, or editorial decision letter unless the user explicitly asks for one.
- Do not invent line numbers, figure panels, datasets, prior studies, or missing analyses.
- Do not cite conversational summaries, author notes, pasted abstracts, or unstored background explanations as evidence.
