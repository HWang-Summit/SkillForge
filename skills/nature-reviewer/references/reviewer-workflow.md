# Reviewer workflow

## Default execution order

1. Identify the task and input package.
   - Confirm this is reviewer-style assessment rather than author rebuttal drafting.
   - Determine whether the accepted evidence is `PDF` or `LaTeX source + PDF visuals`.
   - Treat user chat content only as task routing, file-location, or parameter-selection context.
2. Build the file evidence package.
   - For PDF input, run `mineru-pdf-parse` to produce Markdown and available image resources.
   - For PDF input, run `pdf-render-contact-sheet` to produce page PNGs and a contact sheet.
   - For LaTeX input, inspect the main `.tex`, directly referenced `.tex` files, bibliography files, and referenced figure/table assets.
   - For LaTeX input, inspect the corresponding PDF through `pdf-render-contact-sheet`.
3. Record provenance and boundaries.
   - List files used as evidence, parsed text output, visual output, missing files, unreadable pages, parsing failures, or layout anomalies.
4. Build a manuscript fact base from accepted files only.
   - Extract the central claim, key evidence, stated significance, implied audience, and visible limitations.
5. Check assessment readiness.
   - Mark what can be assessed versus what remains missing.
   - If evidence is incomplete, preserve momentum but label uncertainty instead of blocking unless the gap is total.
6. Review the manuscript across the source-grounded axes.
   - Apply `originality`, `scientific importance`, `interdisciplinary interest`, `technical soundness`, and `readability for nonspecialists`.
7. Generate `3` reviewer reports with different emphasis.
   - Use the same fact base for all three reports.
   - Do not invent different reviewer identities or hidden information.
8. Generate a cross-review synthesis.
   - Summarize consensus, points of emphasis divergence, and the most decision-relevant technical and significance risks.
9. Run final QA.
   - Check file provenance, groundedness, consistency, coverage, and non-invention.

## Input handling

- Acceptable review evidence is limited to:
  - manuscript PDF files;
  - MinerU Markdown and image resources derived from manuscript PDFs;
  - rendered PDF page PNGs, contact sheets, and selected single-page PNGs;
  - LaTeX source packages and their corresponding rendered PDF visuals.
- If the user provides only pasted manuscript text, abstracts, figure legends, summary notes, or claims in chat, do not review. Ask for an accepted file input.
- If accepted files are incomplete, partially parsed, or visually suspicious, provide a bounded review and state the assessment boundary.
- If a LaTeX package has no corresponding PDF and no clear local build entrypoint, ask for the PDF before reviewing.

## PDF evidence workflow

1. Confirm the PDF path.
2. Use `mineru-pdf-parse` in the manuscript project root to produce Markdown under `minerU/outputs/`.
3. Use `pdf-render-contact-sheet` to produce `rendered_pdf_pages/page-*.png` and `rendered_pdf_pages/contact.png` or an equivalent output directory.
4. Inspect the MinerU Markdown for claims, evidence, figures, methods, and limitations.
5. Inspect the contact sheet for page order, missing pages, blank pages, truncated content, figure/table visibility, and layout anomalies.
6. Open selected single-page PNGs only when the contact sheet suggests an issue or a figure/page needs closer visual confirmation.

## LaTeX evidence workflow

1. Identify the main `.tex` file from the user-supplied path or local project conventions.
2. Read the main `.tex`, directly referenced `\input` / `\include` files, bibliography files, and referenced figure/table assets when available.
3. Locate the corresponding PDF. Prefer an existing manuscript PDF in the LaTeX project output or build directory.
4. Run `pdf-render-contact-sheet` on the corresponding PDF and inspect the contact sheet before writing the review.
5. If source and PDF appear inconsistent, mark this in the assessment boundary and ground claims in the explicit file evidence that was actually inspected.

## Fact-base extraction checklist

- Extract these items before writing the reports:
  - `manuscript type or apparent submission posture`
  - `main claim`
  - `key evidence presented`
  - `claimed significance`
  - `likely interested readership from the text`
  - `visible technical gaps`
  - `readability or framing issues for nonspecialists`
  - `file provenance for the claim/evidence summary`

## Cross-review generation rule

- The cross-review synthesis should consolidate, not average away, reviewer differences.
- It must separate:
  - shared strengths
  - shared technical concerns
  - differences in significance weighting
  - differences in readership/readability judgment

## Failure-safe behaviour

- When evidence is absent, say the case is not yet established from the accepted file evidence.
- When significance is unclear, distinguish `potentially interesting` from `demonstrated broad importance`.
- When readability is weak, describe the barrier to nonspecialist comprehension instead of rewriting the manuscript unless asked.
- When only chat-based manuscript claims are available, request accepted manuscript files instead of producing a review.
- When PDF parsing fails but page renderings are available, do not infer detailed scientific content from visuals alone; provide only a narrow visual/readability boundary or request a parseable/source file.
- When page rendering fails but parsed text is available, review only the parsed content and mark that visual evidence, figures, and layout could not be assessed.
