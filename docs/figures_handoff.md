# Figures Handoff

Five figures generated for the report. Files at `data/figures/`. This document is the
handoff for the report-drafting chat to place them in the LaTeX source. All numbers in all
figures trace directly to results tables in docs/results.md and to the values in the locked
formal scaffold.

| File | Description |
|---|---|
| `fig1_per_dimension_gap.pdf/.png` | Per-dimension matched-pair means |
| `fig2_ablation_cell_means.pdf/.png` | Six-cell ablation, horizontal bars |
| `fig3_persuasion_by_spec.pdf/.png` | Persuasion pilot by action spec |
| `fig_main_finding.pdf/.png` | Two-bar summary of main BI violation |
| `fig_ablation_effects.pdf/.png` | Four-bar surface-transformation effects |

---

## Figure 1: Per-dimension matched-pair gap

**File:** `data/figures/fig1_per_dimension_gap.pdf` (PNG preview at
`data/figures/fig1_per_dimension_gap.png`)

### Recommended LaTeX placement

Place in the **main results section (§4.1)**, immediately after the per-dimension breakdown
table (Table 1a in docs/results.md, which contains the same six means). The figure should
appear **after** the table, not before — the table carries the exact numbers and BH-adjusted
p-values; the figure makes the magnitude pattern visible at a glance.

### Recommended `\includegraphics` width

```latex
\includegraphics[width=\linewidth]{figures/fig1_per_dimension_gap}
```

Single-column NeurIPS format: `\linewidth` fills the column width (approx. 3.25 in), but the
figure was generated at 6.0 in. At `\linewidth`, text will be slightly smaller than at
generation size. If the journal uses double-column with a 6.5-in full-width option, use
`width=0.9\linewidth` in a `figure*` environment.

### Suggested caption

```
Per-dimension matched-pair means of $\bar{J}_k$ on the matched-pair set ($n_\mathrm{pairs} = 17$).
All six dimensions show $\tau_L$ exceeding $\tau_S$; all six contrasts survive
Benjamini--Hochberg correction at FDR = 0.05 (Table~\ref{tab:per_dim_gap}).
```

### Suggested label

```latex
\label{fig:per_dim_gap}
```

### Prose to update

The prose in §4.1 that introduces the per-dimension breakdown table should be updated to
add: "Figure~\ref{fig:per_dim_gap} plots the per-dimension means for both conditions." Place
this sentence immediately after the table reference.

---

## Figure 2: Ablation cell means (headline figure)

**File:** `data/figures/fig2_ablation_cell_means.pdf` (PNG preview at
`data/figures/fig2_ablation_cell_means.png`)

### Recommended LaTeX placement

Place in **§4.2 (ablation decomposition)**, immediately **before** the ablation contrast
table (Table 2b in docs/results.md). Figure 2 is the visual anchor for the entire ablation
section — it encodes both the cell magnitudes and the color-split pattern (which encodes
surface-text richness, not source). Readers should see the figure before the numbers.

### Recommended `\includegraphics` width

```latex
\includegraphics[width=\linewidth]{figures/fig2_ablation_cell_means}
```

This is the most important figure in the paper. If the journal allows a slightly wider figure
at the top of the results section (e.g., in a full-width slot), use `width=0.95\linewidth`
with `\centering`.

### Suggested caption

```
Cell means of $\bar{J}$ across the six ablation conditions ($n_\mathrm{pairs} = 17$ per
cell). Cells are sorted by ascending mean. The color encodes surface-text richness: cells
with substantive rationale text (bottom three, blue) cluster near the LLM baseline at 4.74;
cells with rationale absent or neutralized (top three, tan) cluster near or below the
scripted baseline at 3.01. Dashed vertical lines mark the two reference levels. Error bars
show $\pm 1$ standard deviation.
```

### Suggested label

```latex
\label{fig:ablation_cells}
```

### Prose to update

- The opening sentence of §4.2 that describes the six conditions should conclude with
  "see Figure~\ref{fig:ablation_cells}."
- The sentence in §4.2 describing the surface-text story ("the color split reflects
  surface-text richness, not source") will be made concrete by cross-referencing
  Figure~\ref{fig:ablation_cells}.

---

## Figure 3: Persuasion cell means by action specification

**File:** `data/figures/fig3_persuasion_by_spec.pdf` (PNG preview at
`data/figures/fig3_persuasion_by_spec.png`)

### Recommended LaTeX placement

Place in **§4.3 (persuasion pilot)**, immediately after the per-spec cell-means table
(Table 3a in docs/results.md). The figure comes after the table to let the table carry the
exact values and standard deviations. The figure makes the cross-spec consistency of the
persuader $>$ vanilla $>$ scripted\_wrapped ordering visually obvious.

### Recommended `\includegraphics` width

```latex
\includegraphics[width=0.9\linewidth]{figures/fig3_persuasion_by_spec}
```

The figure is 5.5 in wide at generation. At `0.9\linewidth` in a single-column format it
will be slightly narrower. The three-group layout benefits from a bit of whitespace on either
side, so `0.9\linewidth` is preferable to `\linewidth` here.

### Suggested caption

```
Persuasion pilot cell means by action specification ($N = 10$ per cell). The ordering
persuader $>$ vanilla\_baseline $>$ scripted\_wrapped holds across all three specifications.
The (\textit{all\_cooperate}, persuader) cell sits exactly at the Likert ceiling on every
replicate ($\mathrm{sd} = 0$). Y-axis is truncated to $[4.4, 5.0]$ to resolve the small
within-spec differences; all six pairwise contrasts within specification are significant at
$p < 0.05$ by Mann--Whitney U (Table~\ref{tab:persuasion_contrasts}).
```

### Suggested label

```latex
\label{fig:persuasion_spec}
```

### Prose to update

The sentence in §4.3 that introduces the three-spec summary should conclude with
"Figure~\ref{fig:persuasion_spec} plots all nine cells." Also, the paragraph that notes the
all\_cooperate ceiling effect should cross-reference Figure~\ref{fig:persuasion_spec} where
the zero-error-bar persuader bar is visually prominent.

---

## Notes on judgment calls

The following choices deviate from or extend the brief; flag to the report-drafting chat if
any need revision:

1. **matplotlib installation.** matplotlib was not in `requirements.txt` (the project uses
   Plotly for the Streamlit dashboard). It was installed into the venv for figure generation.
   If requirements.txt should be updated to include `matplotlib>=3.10`, that is a one-line
   change. Not done here to keep this pass figure-generation only.

2. **Figure 3 legend position.** The brief specifies "Legend at top." The legend was placed
   at `lower right` instead. At `upper left/right`, the legend overlaps with the bars (which
   reach y = 4.86–5.00) and the Likert ceiling reference line at y = 5.0. Lower right is
   clear of all data. If the report format requires top placement, switch to
   `loc='upper left'` and slightly widen the figure to 6.0 in.

3. **mathtext symbols rendered via STIX font.** The brief asked for `\varnothing` and
   `\tilde{r}` as superscripts in Figure 2 labels. Both rendered correctly with
   `mathtext.fontset = "stix"`. No fallback to plain-text labels was needed. The symbols
   display as: $\tau_L^{\varnothing}$ (total-strip cell) and $\tau_L^{\tilde{r}}$
   (neutral-rewrite cell).

4. **Figure 2 error bars.** The brief says to use standard deviation as "a visual indicator
   of within-cell spread" with "subtle" caps. Cap size = 3 pt, cap thickness = 0.8 pt.
   The τ_S (scripted_minus_r) cell has the widest bar (sd = 0.45); its error bar extends
   from 2.56 to 3.46, which is visible and appropriate given the genuine cell spread.

5. **Figure 3 y-axis.** Set to [4.4, 5.15] rather than [4.4, 5.0] to give headroom above
   the Likert ceiling line and allow the ceiling label text to be readable. The 5.0 dashed
   reference line is clearly visible within this range.

6. **Figure 1 does not include error bars.** The brief did not specify error bars for
   Figure 1, and no standard deviations are provided for the per-dimension matched-pair
   means in the brief's source data table. Error bars were omitted. If the per-pair
   standard deviations are needed, they can be recomputed from the database via the same
   queries used in the results analysis.

---

## Figure A: Main finding — two-bar summary

**File:** `data/figures/fig_main_finding.pdf` (PNG preview at
`data/figures/fig_main_finding.png`)

**Source data:** Table 2 of the report — $\bar{J}(\tau_L) = 4.7353$ (sd 0.1358),
$\bar{J}(\tau_S) = 3.0882$ (sd 0.4274), $n_\text{pairs} = 17$.

### Recommended LaTeX placement

Place in **§1.3 (Contributions)**, after the first sentence of the second paragraph — the
sentence that states $\hat{\Delta} = +1.6471$. Figure A is a teaser visual; readers should
see the magnitude of the gap immediately after reading the headline number, before any
methodological detail. Placement: **after** the $\hat{\Delta}$ sentence, **before** the
paragraph on surface features.

### Recommended `\includegraphics` width

```latex
\includegraphics[width=0.7\linewidth]{figures/fig_main_finding}
```

The figure is 5.0 in wide at generation. At `0.7\linewidth` in a 3.25-in single-column
format it renders at ~2.3 in, which is compact and suitable for an introductory visual.

### Suggested caption

```
Main finding: aggregate judge score $\bar{J}$ by transcript source on the matched-pair set
($n_\mathrm{pairs} = 17$). The empirical estimate of $\hat{\Delta}$ is $+1.6471$ on the
one-to-five aggregate scale (Wilcoxon two-sided $p = 2.91 \times 10^{-4}$, matched-pair
Cohen's $d = +3.61$). Error bars show $\pm 1$ standard deviation. Dashed line marks the
Likert midpoint.
```

### Suggested label

```latex
\label{fig:main_finding}
```

### Prose to update

The existing sentence in §1.3 reporting $\hat{\Delta}$ should be updated to append
"(Figure~\ref{fig:main_finding})." This is the only required prose edit; the figure is
self-explanatory at the §1.3 level of detail.

---

## Figure B: Surface-transformation effects (ablation)

**File:** `data/figures/fig_ablation_effects.pdf` (PNG preview at
`data/figures/fig_ablation_effects.png`)

**Source data:** Table 5 of the report — $T_{+r} = +1.6324$, $T_\varnothing = -2.4314$,
$T_{\tilde{r}} = -2.1078$, $T_{-r} = -0.0049$. All from $n_\text{pairs} = 17$.

### Recommended LaTeX placement

Place in **§5.2 (ablation decomposition)**, immediately **before** Table 5 (the within-condition
contrast table). Figure B is the visual complement to the Wilcoxon contrast table — readers
should see the direction and magnitude pattern before reading the exact numbers. The paragraph
that introduces the four transformation maps ($T_{+r}$, $T_\varnothing$, $T_{\tilde{r}}$,
$T_{-r}$) should end with a forward reference to Figure B, then the figure, then Table 5.

### Recommended `\includegraphics` width

```latex
\includegraphics[width=\linewidth]{figures/fig_ablation_effects}
```

Full single-column width. The figure is 6.5 in at generation — at `\linewidth` (3.25 in) the
text inside bars will be proportionally reduced; verify readability in proof. If text becomes
too small at single-column width, switch to a `figure*` full-width environment with
`width=0.75\linewidth`.

### Suggested caption

```
Surface-text ablation decomposes the matched-pair gap. The within-scripted rationale wrap
$T_{+r}$ closes the gap from below by $+1.6324$ on $\bar{J}$; the two within-LLM
rationale removals ($T_\varnothing$, $T_{\tilde{r}}$) open it from above by 2.4314 and
2.1078. The marker-list strip $T_{-r}$ produces no shift, identifying judge sensitivity as
structural rather than lexical. All effects on the same $n_\mathrm{pairs} = 17$ matched
index. *** indicates $p < 0.001$ by paired Wilcoxon signed-rank; ns indicates $p = 0.97$.
```

### Suggested label

```latex
\label{fig:ablation_effects}
```

### Prose to update

Two edits:

1. The paragraph that introduces Table 5 should end with: "Figure~\ref{fig:ablation_effects}
   visualises the four transformation effects."
2. The sentence describing $T_{+r}$ closing the gap should append:
   "(the positive blue bar in Figure~\ref{fig:ablation_effects})."

### Notes specific to Figure B

- **Null bar visibility.** The $T_{-r}$ bar has effect $-0.0049$ on a $[-3, 2.5]$ scale —
  the filled rectangle is sub-pixel. A thin gray edge is drawn at $y = 0$ to make the
  "effectively zero" bar traceable. The numeric label and "ns" marker above $y=0$ are the
  primary communication; the edge is a secondary cue.
- **Descriptor text.** The brief specified single-line descriptors in parentheses
  (e.g., "(scripted α + LLM rationale)"). These were split into two-line annotations
  ("scripted α / + LLM rationale") placed below the x-axis to prevent horizontal overlap at
  the 6.5-in figure width. The semantic content is unchanged.
- **Callout text.** The sentence above the chart reads verbatim: "Adding LLM-style rationale
  to scripted transcripts closes the gap. Removing rationale from LLM transcripts opens it.
  Lexical-marker strip has no effect." This is freshly authored — the teammate's earlier draft
  phrasing is not reproduced.
- **Color consistency.** PRIMARY (#2E5C8A) and SECONDARY (#B08968) were verified by pixel
  sampling against the existing figures before generation. ACCENT_RED (#C25450) and
  NULL_GRAY (#9C9C9C) are new to Figure B and do not conflict with the existing palette.
