# Mathematical reasoning supplement — WaterSense and AquaVision

**Status:** AI-assisted V4 technical explanation prepared on 2026-10-14. It is not a historical derivation by the project owner and requires the owner’s mathematical review before public use. Theory below is separated from observed project results.

## 1. WaterSense

### Weighted regression loss

For observations `i=1,…,n`, target dissolved oxygen `y_i`, prediction `f(x_i)`, and low-DO threshold `τ=4`, the v3 sample weight is

`w_i(m) = m` if `y_i < τ`, otherwise `1`, followed by normalization `w'_i = w_i / mean(w)`.

A weighted squared-error estimator minimizes

`L(f;m) = (1/n) Σ_i w'_i(m) [y_i − f(x_i)]²`.

Normalization leaves relative weights unchanged but stabilizes the average scale. The target is used only to construct training-fold weights. In the formal v3 experiment `m ∈ {1,2,4,8}`. This formula explains a mechanism; it does not prove that weighting caused every observed change because the outer selected procedure also changed estimator settings.

### Station-grouped and nested cross-validation

Let `g(i)` be the station for row `i`. A grouped partition requires

`{g(i): i ∈ Train_k} ∩ {g(i): i ∈ Validation_k} = ∅`.

Nested CV adds an inner split inside each outer-training set. If `λ` indexes a candidate, then

`λ̂_k = argmin_or_rank_λ InnerScore_k(λ)`

is chosen without outer fold `k`, and the outer estimate is computed only on `Test_k`. Concatenating the five outer predictions gives one out-of-fold prediction per development row. This estimates a complete selection procedure; it is not external confirmation.

### Cluster bootstrap

Rows within a station are dependent. For stations `s=1,…,S`, a cluster bootstrap draws `S` station IDs with replacement and includes every row belonging to each drawn station. For paired models A and B, replicate `b` computes `Δ_b = M_B^(b) − M_A^(b)` on the same sampled clusters. Percentiles of `{Δ_b}` form an empirical interval. This respects station clustering but cannot create geographic independence or correct nonrepresentative sampling.

### Recall, precision, and costs

With low DO as positive: `Recall = TP/(TP+FN)`, `Precision = TP/(TP+FP)`, and `F1 = 2PR/(P+R)`. The V4 classifier had `TP=699`, `FN=59`, and `FP=9517`, giving Recall `699/758 = 0.9222`, Precision `699/10216 = 0.0684`, and F1 `0.1274`. High recall therefore did not imply useful precision.

For hypothetical costs, `C = C_FN·FN + C_FP·FP`. At `C_FN:C_FP=10:1`, the v3 procedure costs `10·482+219=5,039`, lower than the fixed regression baseline’s `6,626` and classifier’s `10,107`. At 25:1, the classifier costs `10,992`, lower than v3’s `12,269`. These are scenario calculations, not real regulatory valuations.

## 2. AquaVision

### Macro F1 and class imbalance

For class `c`, `F1_c = 2 P_c R_c/(P_c+R_c)`, with zero contribution under the project’s fixed three-class rule when a class is unsupported or never retrieved as specified by the frozen evaluator. Three-class Macro F1 is `(F1_Low + F1_Moderate + F1_High)/3`. It gives each class equal arithmetic weight, whereas pixel accuracy can be dominated by abundant Low pixels. Macro averaging does not solve missing independent High waterbodies.

### Spatial autocorrelation and geographic leakage

Spatial autocorrelation means nearby observations have correlated values. A common descriptive statistic is Moran’s `I = (N/W) [Σ_i Σ_j w_ij(z_i−z̄)(z_j−z̄)] / [Σ_i(z_i−z̄)²]`, where `w_ij` encodes spatial proximity and `W=Σ_iΣ_jw_ij`. If nearby crops cross Train/Test, effective information overlap can remain even when filenames differ. AquaVision therefore groups touching author-grid windows historically and, prospectively, requires a real waterbody history to stay within one split.

### Proxy-label resolution

CyAN supplies a roughly 300 m proxy grid while Sentinel patches use a finer grid. Nearest-neighbor resampling maps one native label into multiple target pixels but adds no new source measurement. If a patch contains 4,096 target pixels but only 19 valid native CyAN centers, the reference support is 19, not 4,096. The label is also a satellite proxy class, not a measured toxin concentration.

### Effective independent sample units

If `n` correlated observations have an exchangeable within-cluster correlation `ρ`, a heuristic effective sample size is `n_eff ≈ n/[1+(n−1)ρ]`. For `n=4096` and `ρ=0.9`, `n_eff≈1.11`; this numerical illustration is theoretical, not an estimated AquaVision correlation. The project uses a stricter design-based solution: count independent real-waterbody units only after scene, event/date, footprint, native-cell, provenance, and cross-split checks. Six pilot scenes collapse to three waterbody histories, and zero histories pass the full High-support gate.

## 3. Theory versus observation

The equations define estimands and failure mechanisms. The numerical WaterSense confusion counts and AquaVision support counts are observed saved evidence. The effective-sample-size calculation is only an illustration. Neither project establishes a new theorem, causal environmental mechanism, operational threshold, or external confirmation.
