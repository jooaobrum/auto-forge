---
name: feature-ideas
profile: tabular
status: team
---

# Feature engineering ideas for tabular data

Basis: Mario Filho's idea notebook, "Feature engineering ideas for tabular data"
(mariofilho.com, 2025). The article gives only the names. The descriptions and the **Causal?** column are
ours, because in hill climbing every feature goes through CHK-LEAK-003 (the `prepare` step only looks back).

## Questions to generate ideas (from the article)

1. **Group and extract:** for each column, "if I group by this one, what variable can I extract from the
   others?". Then pairs and triples of grouping columns.
2. **Transform by type:** each type has its transformations (categorical -> count, likelihood).
   Expand with sum, max, product and ratio, also in pairs and triples.
3. **Sort:** "if I sort, do I see a pattern?" (by time, by group, by the value itself).
4. **Importances:** see what the model already uses before creating more of the same.
5. **Distribution:** "is the test distribution the same as train?" Here: valid vs train in the EDA,
   OOT only in Verify (CHK-ADV-001).

## Catalog

| Family | Ideas | Causal? (our note) |
| --- | --- | --- |
| Group statistics | mean, max, min, std, variance, skewness, kurtosis, sum of the variable within the group | only with earlier rows of the group: `groupby(g)[x].transform(lambda s: s.shift(1).expanding().mean())` |
| Count, proportion, ranking | count per category, frequency, share of the total, rank within the group, ordinal encoding | counts and ranks accumulated up to the row; frequency over the whole dataset sees the future |
| Class proportion in the group | target rate per category/group (likelihood / target encoding) | **leaks** outside the pipeline; use `TargetEncoder` inside the pipeline (inner CV) or the target mean of past rows only |
| Math transformations | log, sqrt, x^2, 1/x, -1/x, 1/log(x), exp, logit, pseudo-log (`asinh`), trigonometric | row by row, always causal |
| Normalization | z-score, min-max, rank | fit inside the pipeline (scaler) or with a statistic from the past |
| Temporal | x per period, x in the last N periods, percentage change, change over +-N periods, time between actions, gap between actions, time since an event, time discount, lags, trend and detrending, velocity, rate of change | lags and backward windows are causal; "+N periods" and centered windows **leak** |
| Categorical and binning | one-hot, binning, binning + one-hot, category embeddings, grouping rare categories | binning limits and "rare" learned in the pipeline |
| Reduction and complex features | PCA, t-SNE, tree leaves as a feature, out-of-fold transformation, graph metrics | inside the pipeline; out-of-fold is the default for stacking models |
| Interactions and relations | difference between columns, difference between correlated features, `corr(x1, x2)` by `x3`, sorted differences, duplicating columns for interaction, dependence across rows | row by row is causal; dependence across rows only with earlier rows |
| Duplicates | flag or count duplicates | count only earlier duplicates |
| Density and distance | local density, distance to a reference point, cosine distance to the mean profile, CDF | the mean profile and the CDF fit on train (pipeline) |
| Signals and series | smoothing, FFT, Savitzky-Golay | causal filters (past only); the default Savitzky-Golay is centered and **leaks** |
| Others | entropy, hierarchical/cluster, deviation (from mean, from trend), sequence | depends on how it is computed; the iteration's CHK-LEAK-003 tells |

## How to test an idea

1. In the EDA ([eda.md](../eda.md)), on **train**: the feature's relation with the target, per period.
   Cheap, and it saves spending an iteration.
2. In hill climbing: one family per iteration, on top of the current best. The judge decides with a CI.
3. A rejected idea with a clear mechanism becomes a lesson ("the batch mean does not help: the batch does not explain the failure").
