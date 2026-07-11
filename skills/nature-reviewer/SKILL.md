---
name: nature-reviewer
description: >-
  Simulate a Nature-style reviewer assessment from the referee perspective rather than
  an author rebuttal. Use when the user wants a pre-submission review, reviewer report,
  peer-review style critique, novelty/significance/technical soundness assessment,
  reviewer-style manuscript evaluation, 审稿人视角评估, 预审稿意见, or Nature reviewer
  report. Return 3 reviewer reports plus a cross-review synthesis, grounded only in the
  local Nature reviewer source basis and file-derived manuscript evidence. For PDF
  manuscripts, parse the PDF with mineru-pdf-parse and inspect PDF page thumbnails with
  pdf-layout-inspection before reviewing. For LaTeX manuscripts, review the LaTeX
  source plus the corresponding PDF thumbnails.
  Also trigger on general pre-submission review requests during academic writing even without the
  word "Nature", such as getting a mock peer review for any journal, critiquing a draft as a
  reviewer would, assessing novelty/rigor before submission, and Chinese phrasings like
  审稿人视角、模拟审稿、预审、帮我审一下论文、投稿前自审、审稿意见模拟、找论文问题.
version: 0.1.0
status: Draft
---

# Nature Reviewer Assessment Skill

Use this skill to simulate a `Nature`-style reviewer assessment package from the referee
side.

This skill is for reviewer-style manuscript evaluation, not for drafting the authors'
response. If the user wants rebuttal writing, route to `nature-response`.

## Default stance

- Ground the review only in the local source basis plus manuscript facts extracted from accepted files.
- Treat user chat text only as task routing, file-location, or parameter-selection context; do not use it as manuscript evidence.
- Evaluate the manuscript against source-grounded axes: `originality`, `scientific importance`, `interdisciplinary readership`, `technical soundness`, and `readability for nonspecialists`.
- Return exactly `3 reviewer reports + 1 cross-review synthesis` unless the user explicitly asks for another structure.
- The three reviewers may differ only in `emphasis`; do not invent reviewer identities, specialties, institutions, or biographies.
- Identify who would be interested in the results and why.
- Identify technical failings that must be addressed before the authors' case is established.
- Distinguish clearly between what is supported, what is weak, and what is not assessable from the accepted file evidence.
- Do not claim the editor's final decision or certainty about fit to `Nature`.

## Accepted inputs

The review evidence package may contain only these file-derived inputs:

- a manuscript PDF file;
- MinerU Markdown and image resources derived from that PDF;
- PDF page renderings, contact sheets, or selected single-page PNGs derived from that PDF;
- a LaTeX source package, including the main `.tex`, directly referenced `.tex` files, bibliography files, and referenced figure/table assets;
- a PDF rendering of the LaTeX manuscript and its contact sheet or selected single-page PNGs.

If the user supplies only pasted text, abstract text, author notes, or conversational claims, do not perform the review. Ask for a PDF manuscript or a LaTeX source package with the corresponding PDF. If accepted files are partial or cannot be fully parsed, perform only a bounded review and mark the assessment boundary explicitly.

## Workflow

1. Identify whether the job is a reviewer-style assessment rather than rebuttal drafting.
2. Build the file evidence package.
   - For a PDF manuscript, invoke `mineru-pdf-parse` to create Markdown and extracted resources, then invoke `pdf-layout-inspection` to create page PNGs and a contact sheet.
   - For a LaTeX manuscript, read the source package and inspect the corresponding PDF through `pdf-layout-inspection`; if no corresponding PDF exists and the build entrypoint cannot be determined, ask for the PDF before reviewing.
3. Record the evidence boundary: input type, files used, parse output, visual review output, missing files, unreadable pages, parsing failures, or layout anomalies.
4. Extract a shared manuscript fact base from accepted files only: main claim, visible evidence, claimed significance, likely readership, and visible limitations.
5. Check readiness and label missing evidence or missing sections instead of inventing them.
6. Assess the manuscript using the source-grounded axes.
7. Generate `Reviewer 1`, `Reviewer 2`, and `Reviewer 3` using shared facts but different emphasis.
8. Generate a `Cross-review synthesis` that captures consensus and weighting differences.
9. Run QA for file provenance, groundedness, coverage, role boundaries, and non-invention.

## Output format

Unless the user asks for another format, return:

```text
Review setup
- Input package:
- Files used as evidence:
- Parsed text source:
- Visual review source:
- Assessment boundary:
- Shared manuscript claim summary:
- Visible evidence base:
- Missing materials affecting confidence:

Reviewer 1
- Overall assessment:
- Who would be interested in the results, and why:
- Major strengths:
- Major concerns:
- Technical failings that need to be addressed before the case is established:
- Assessment against Nature-style criteria:
- Recommendation posture:

Reviewer 2
[Same structure]

Reviewer 3
[Same structure]

Cross-review synthesis
- Consensus strengths:
- Consensus technical risks:
- Where emphasis differs across reviewers:
- Broad-interest / significance readout:
- Most important issues to resolve before a strong Nature-style case is established:

Risk / unsupported claims
- [specific unsupported or not-assessable items]
```

## Red lines

- Do not invent reviewer identities, specialty roles, or selection history.
- Do not invent experiments, validations, controls, citations, figure details, line numbers, or prior-work distinctions not present in the input.
- Do not use user-supplied conversational summaries, claims, notes, or background explanations as manuscript evidence.
- Do not silently turn reviewer assessment into author rebuttal drafting.
- Do not present the review as an editorial decision letter.
- Do not state that the manuscript belongs in `Nature` as a settled fact.
- Do not omit technical failings when the accepted file evidence does not establish the authors' case.

## Related files

| File | Open when |
|---|---|
| [references/source-basis.md](references/source-basis.md) | You need source provenance, local rule summaries, or source-vs-implementation boundaries |
| [references/reviewer-workflow.md](references/reviewer-workflow.md) | You need the invocation order, fact-base extraction flow, or synthesis rules |
| [references/review-axes.md](references/review-axes.md) | You need the evaluation axes or reviewer weighting logic |
| [references/report-structure.md](references/report-structure.md) | You need the default output contract or section anatomy |
| [references/role-boundaries.md](references/role-boundaries.md) | You need constraints on reviewer differences and editor-versus-reviewer boundaries |
| [references/qa-checklist.md](references/qa-checklist.md) | You are finalizing an output and need groundedness / non-invention checks |
| [references/editorial criteria and processes.md](references/editorial criteria and processes.md) | You need the primary local Nature source text |

## Source hierarchy

Use sources in this order:

1. `references/editorial criteria and processes.md`
2. manuscript facts extracted from accepted files
3. conservative local implementation rules documented in `references/source-basis.md`

If a user asks for policy-level certainty beyond this local source, state the limit instead of improvising broader journal policy.
