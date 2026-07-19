# Pitfalls Research

**Domain:** Thermal-to-geometry prediction in directed energy deposition (DED) laser manufacturing — multimodal (thermal/SEM/profilometry) ML competition pipeline, 8-day sprint, 4 track conditions, local GPU
**Researched:** 2026-07-19
**Confidence:** MEDIUM-HIGH (codebase-grounded findings are HIGH confidence — verified directly against `src/nsf_fmrg_data.py`; general ML/metrology community pitfalls are MEDIUM confidence per web search; a few forward-looking inferences about untested failure modes are flagged explicitly as reasoned, unverified predictions)

## Critical Pitfalls

### Pitfall 1: SEM target leakage — processed track region visible to the model

**What goes wrong:**
The model is fed SEM substrate imagery that includes pixels from the final, already-processed laser track (melt pool trace, resolidified bead, heat-affected zone). Because the SEM tile literally shows the final track shape, any model given unmasked SEM input can trivially "predict" width/boundary by reading it directly off the image rather than learning a thermal→geometry relationship. Reported accuracy on this leaked channel will look excellent and will not transfer to true held-out prediction (organizers evaluate against the same measured height maps, so a model this leaky will simply reproduce ground truth on masked-out combos it saw and fail elsewhere).

**Why it happens:**
SEM tiles are the *only* source of "substrate context" data, and the definition of "processed track region" is not organizer-supplied as a ready mask — it must be derived from physical coordinates and hand-tuned per track. Under time pressure, teams either skip masking (feed raw stitched SEM) or mask too loosely (mask width narrower than actual bead width, especially for the 400W track which has the largest melt pool).

**How to avoid:**
- Define the mask in **physical coordinates** (mm), centered on the nominal scan path, with a safety margin — per organizer clarification, applied identically to every track (do not hand-tune per track, which itself risks encoding track identity).
- Set mask half-width generously larger than the *widest* observed/expected track width across all 4 powers (400W will have the largest melt pool — use it, not the median, to size the margin so no part of any track's final geometry leaks through, even under measurement/alignment tolerance).
- Visually overlay the mask on the stitched SEM mosaic and the height-map track outline for all 4 tracks before using it in any model — confirm zero overlap by eye, not just by formula.
- Treat masking as a gate: no SEM-fused model may be trained until the mask has been visually verified against all 4 tracks.

**Warning signs:**
- SEM-fused model dramatically outperforms the thermal-only baseline (order-of-magnitude drop in MAE) — a huge, suspiciously easy win is the classic leakage tell.
- Feature-importance / ablation shows the model relies heavily on SEM pixels directly under the nominal scan path.
- Visual inspection of a masked SEM patch still shows a visible bead/track edge inside the "unmasked" region.

**Phase to address:**
Must be resolved inside the SEM stitching + masking utility (stretch scope, per PROJECT.md), before any SEM-fused model variant is trained. Since this is explicitly stretch/deferred until after the thermal-only baseline ships, gate it behind a mandatory visual-verification checkpoint, not just code review.

---

### Pitfall 2: Spatial-correlation leakage from splitting neighboring positions within a track

**What goes wrong:**
Randomly splitting spatial positions `x_j` within the same track into train/test (or doing k-fold CV over all positions pooled across tracks) puts near-neighbor positions in both sets. Because the melt pool and substrate morphology change smoothly and slowly along the scan direction, adjacent positions (≈0.2 mm apart) are almost duplicate samples. A model can memorize local track segments rather than learning a generalizable relationship, and validation MAE looks artificially low — a textbook case of the exact leakage mode documented broadly in the geospatial-ML and ecology cross-validation literature (spatially autocorrelated data + random splits + inflated held-out scores) ([Fair train-test split in ML: mitigating spatial autocorrelation](https://www.sciencedirect.com/science/article/abs/pii/S0920410521015023), [Spatial cross-validation using scikit-learn](https://towardsdatascience.com/spatial-cross-validation-using-scikit-learn-74cb8ffe0ab9/)).

**Why it happens:**
It is the natural, easy thing to do with a windowed-frame dataset (thousands of `(thermal window, x, width)` samples once tracks are chunked into positions) — standard `train_test_split(shuffle=True)` or standard k-fold silently treats spatially adjacent rows as independent, and nothing in the data format warns you otherwise.

**How to avoid:**
- Leave-one-track-out (organizer-confirmed and PROJECT.md-mandated) is the *only* valid outer validation split — never split by position/frame index within a track.
- The same rule applies recursively to any inner validation used for early stopping / hyperparameter tuning: hold out an *entire track* (not a random subset of positions) from the 3 remaining training tracks, or use nested leave-one-track-out.
- Any reported metric that isn't computed on a fully unseen track (all its positions absent from training) should be labeled clearly as "in-track validation, optimistic" and never used as the headline number.

**Warning signs:**
- Validation curves that look "too good" (near-zero MAE) using any split that pools positions across a single track.
- A large gap between in-track validation score and true leave-one-track-out score once measured — a strong signal the in-track number was never trustworthy.

**Phase to address:**
Must be caught before the model-training phase begins — build and unit-test the leave-one-track-out harness as its own deliverable (with a "no shuffle-split fallback path" guard) before any model code is written against it.

---

### Pitfall 3: Track identity / laser power as a trivially leaky feature

**What goes wrong:**
With only 4 tracks total, `track_id` (or laser power, which is a 1:1 proxy for track_id: 8=400W, 10=350W, 14=300W, 21=200W) is a near-perfect categorical shortcut. If included as a model feature, a model evaluated with leave-one-track-out CV cannot use it for the held-out track at all (its value there is never seen in training) — but it can still let the model overfit *within* the 3 training tracks by learning "track A → width offset A" instead of a real thermal→geometry mapping, inflating training/in-track metrics without any true generalization benefit, and worse: because power and track are perfectly confounded, the model cannot distinguish "this relationship is true because of laser power" from "this relationship is true because of track-specific quirks" (single track per power = zero power-holding-track-varying replication).
A subtler variant: even *without* an explicit `track_id`/`power` feature, the model can reconstruct track identity from incidental signals that correlate with it — e.g., thermal camera absolute intensity calibration/gain drifting slightly between recording sessions, or the exact number of frames extracted per track — letting it "cheat" via a proxy rather than the intended melt-pool physics.

**Why it happens:**
Laser power (or its derived energy density) is explicitly suggested as a candidate metadata feature by the organizers, and it *is* physically meaningful — the pitfall is not that power is a bad feature, but that with N=4 tracks it is statistically indistinguishable from a track-ID indicator, so its "value" cannot be honestly assessed and its presence can mask overfitting.

**How to avoid:**
- Treat laser power/energy-density as a feature to *report and interpret* (e.g., in ablations, feature-importance discussion for the report) rather than a feature whose inclusion should be tuned to maximize leave-one-track-out score — with N=4, you cannot separate "power helps" from "power identifies the track."
- Run an explicit ablation: model with vs. without power/track metadata, both evaluated via leave-one-track-out. If removing thermal features but keeping only power/track-derived features gives suspiciously competitive accuracy, that's a signal the "real" signal is coming from track identity, not thermal history.
- Do not use absolute (unnormalized) thermal intensity as a feature without checking for cross-track calibration drift; prefer per-track normalized/relative thermal descriptors (e.g., percentile-normalized within a track) as far as is physically defensible, and note in the report if this is not fully avoidable given 4 recording sessions.

**Warning signs:**
- A model using only metadata (track/power, no thermal frames) achieves surprisingly strong leave-one-track-out accuracy — indicates the "geometry" target itself has a large per-track offset component that swamps local spatial variation, or that power/track leak more than intended.
- Feature importance dominated by track/power rather than thermal-derived features.

**Phase to address:**
Feature-engineering / dataset-construction phase — decide up front (and document in the report) how power/track metadata is used, and bake the ablation check into the evaluation phase, not as an afterthought.

---

### Pitfall 4: Cross-track file mismatch via the `find_track_file` substring fallback

**What goes wrong:**
`find_track_file()` in `src/nsf_fmrg_data.py:21-31` matches candidate files with a bounded regex first, but falls back to a bare substring check (`f'{track_id}' in name`) if the regex doesn't match. Track IDs here are 8, 10, 14, 21 — note that `"1"` is a substring of `"14"`, `"21"` is not a substring of the others, but `"8"` could coincidentally appear inside a longer numeric filename, and any future data reorganization (extra files, renamed exports, `.bak`/duplicate copies with different naming) risks the substring fallback silently picking the *wrong* track's thermal/height-map/SEM file. Because loaders return data with no cross-check against an expected track ID inside the file itself, a mismatch would not raise an error — it would silently pair track 14's thermal frames with, say, track 21's height map, corrupting every downstream sample for that "track" without any exception being thrown.

**Why it happens:**
The fallback exists as a leniency measure for filenames that don't match the exact regex, but it trades safety for flexibility, and there is no validation step (e.g., re-parsing the resolved filename or an embedded ID inside the file) to confirm the resolved path truly belongs to the requested track.

**How to avoid:**
- Before building the training dataset, run a one-time integrity check: for each of the 4 track IDs, call `find_track_file` for all three modalities and print/log the resolved path; manually confirm each path's filename matches the expected track exactly (not just "contains" it).
- Tighten the regex-only match (drop the substring fallback, or restrict it to only trigger with a loud warning) once the known filenames are confirmed to already fit the strict pattern — do not rely on silent leniency in a pipeline whose correctness cannot be spot-checked at model-output time.
- Add an assertion inside the data-loading layer that the number of matched thermal/SEM/height-map files per track is exactly 1 (fail loudly on 0 or >1 matches) rather than silently taking the first sorted match.

**Warning signs:**
- Any unexpected track-to-track "improvement" or "degradation" pattern in per-track metrics that doesn't track with laser power monotonically (e.g., 400W and 200W look suspiciously similar) is worth re-checking file identity before debugging the model.

**Phase to address:**
Data-loading / dataset-construction phase — before target extraction or sample-building begins; a 10-minute manual verification here prevents corrupting every downstream artifact.

---

### Pitfall 5: Normalization/statistics computed across all tracks before the split (test-track leakage into preprocessing)

**What goes wrong:**
Even with a correct leave-one-track-out split at training time, it's easy to leak information earlier in the pipeline: e.g., computing global mean/std for thermal-frame normalization, target (width) normalization, or robust-detrending reference statistics using all 4 tracks (including the held-out one) before the split is applied. This "preprocessing leakage" silently gives the model access to the held-out track's distributional properties (its typical width, its typical thermal intensity range) even though no raw samples from it were in the training set.

**Why it happens:**
Preprocessing (normalization, detrending, scaling) is naturally implemented once, up front, over "the whole dataset" for convenience, before train/test are separated in the modeling code — a very common and easy-to-miss ordering mistake.

**How to avoid:**
- Fit any normalization/scaling statistics (mean/std of thermal intensity, width target scaling, etc.) only on the 3 training tracks for each leave-one-track-out fold, then apply those fitted statistics to transform the held-out track — never fit on pooled data that includes the fold's test track.
- Height-map detrending (`robust_plane_detrend`) is a per-track geometric operation (fits within one track's own tilt), so it does not leak across tracks by construction — but any *downstream* target normalization built on top of detrended widths must still respect the fold boundary.

**Warning signs:**
- Normalization code that runs once, before any train/test split object exists, using variables named like `all_tracks` or `full_dataset`.

**Phase to address:**
Target-extraction / dataset-construction phase, verified again at cross-track-validation-harness phase (the harness should assert per-fold-only statistics fitting, e.g., via a lightweight code review checklist item).

---

### Pitfall 6: Noise-sensitive, inconsistently-defined "local width" extraction from height maps

**What goes wrong:**
No organizer-provided extractor exists for `w_i(x)`, so the team must invent one. Common mistakes when turning a raw Bruker/Wyko height map into a local width/boundary signal:
- **Noise amplification:** naive per-column thresholding on raw (non-detrended, non-smoothed) height values turns profilometer noise into false boundary jitter — width traces look like ragged, high-frequency noise rather than the smooth physical variation the task description asks you to preserve ("preservation of spatial variations," an explicit organizer evaluation criterion).
- **Detrending artifacts:** `robust_plane_detrend` fits a single global tilt plane per track using a *coarsely and asymmetrically strided* grid (`stride_x=40, stride_y=2` in `src/nsf_fmrg_data.py:205-227`). A linear-plane fit only removes tilt, not any real low-frequency bow/curvature in the substrate; residual curvature can then be misread as "local width variation" that is actually leftover detrending artifact, not true track geometry signal. The asymmetric stride (dense in y, sparse in x) also means the fit is more sensitive to y-direction structure than x — worth being aware of if track curvature runs along x.
- **Inconsistent absolute thresholds across laser powers:** track widths differ substantially across 400W/350W/300W/200W tracks. A single fixed absolute-height cutoff used to define "track edge" for all 4 tracks will not generalize — it needs a per-cross-section relative definition (e.g., a fixed fraction of local depth drop from the local baseline), not one universal absolute z-value.
- **Inconsistent handling of gaps/NaNs:** track 21 (200W) has explicitly less-complete profilometry coverage than the other 3. If the width-extraction code interpolates over NaNs for the 3 clean tracks but has different (or no) fallback behavior for track 21's larger gaps, the "ground truth" being compared against on the held-out track is computed by a different effective procedure than during training-time validation — an apples-to-oranges evaluation.

**Why it happens:**
Under time pressure, it's tempting to eyeball one track, hand-tune a threshold that looks right, and reuse it everywhere without re-validating on the other 3 — especially because track 21 (the recommended held-out test track) is also the one with the worst data quality, so problems there are least likely to be caught during "does this look right" spot-checks on the training tracks.

**How to avoid:**
- Smooth (e.g., low-order polynomial or Savitzky-Golay along `x`) the extracted boundary/width signal at a bandwidth chosen deliberately, and document the choice — but do not over-smooth to the point of erasing real local variation (defeats the "predict locally" goal).
- Define track edges via a **relative** criterion (fraction of local peak-to-baseline depth, or a per-cross-section z-score) rather than one fixed absolute height value, so the same definition is physically meaningful across all 4 very different track widths/powers.
- Explicitly document and unit-test the same extraction function against all 4 tracks, including specifically the gap-heavy regions of track 21, before treating any target as final.
- Consider whether a purely linear plane detrend is adequate; visually check post-detrend residual maps on all 4 tracks for obvious remaining bow/curvature before locking in the target-extraction method.

**Warning signs:**
- Extracted width signal has high-frequency "sawtooth" jitter that doesn't look like a physically smooth process.
- Width or boundary values near the two ends of the 20mm/100mm window jump/discontinue relative to the interior.
- The extraction method was tuned by eye on one track only (typically track 8, the highest-power/most-complete data) and never re-validated visually against track 21.

**Phase to address:**
Target-extraction phase — this is the first Active requirement in PROJECT.md and gates everything downstream; it must be validated (visually, on all 4 tracks) before the model-training phase begins, precisely because "no organizer-provided extractor exists" and an invalid target invalidates every subsequent metric.

---

### Pitfall 7: Edge effects near the 20mm/100mm window boundaries

**What goes wrong:**
The shared analysis window (20–100mm) is a crop, not a natural physical boundary of the process — the laser continues before 20mm and after 100mm in the full scan. Width/boundary-extraction methods that use any kind of local neighborhood (smoothing kernel, rolling window, edge-detection stencil) will behave differently right at `x=20mm` and `x=100mm` than in the interior, because there is no data just outside the crop to support a centered window — the classic boundary-effect problem in any windowed signal processing. Separately, the *thermal* extraction is entirely different: it locates the window by detecting the laser-on/off transition and taking the *last* `EXTRACTED_THERMAL_FRAMES` frames before shutoff (`extract_final_thermal_frames`, `src/nsf_fmrg_data.py:114-130`), which assumes shutoff coincides tightly with 100mm — any timing slop here shifts the thermal window relative to the height map/SEM crop, most severely visible right at the window edges.

**Why it happens:**
Analysts often build boundary-extraction and smoothing code without special-casing edges, and the shared window is a data-provider convenience, not a physically distinguished region — the process behavior at the true start/stop of the raster (near 20mm/100mm) can also be transient (laser ramp-up/settling), not representative steady-state track formation, and this reads as "just more of the same signal" unless explicitly flagged.

**How to avoid:**
- Use asymmetric/edge-aware smoothing (e.g., reflect or truncate kernels at the boundary, or use `mode='valid'`/report NaN rather than fabricating extrapolated values) rather than kernels that silently assume data exists past the crop.
- Explicitly flag or exclude the first/last few hundred microns to few mm of the analysis window from headline metrics if visual inspection shows transient/edge artifacts, and note this in the report so judges see it as a deliberate methodological choice rather than a bug.
- Cross-check the thermal-window boundary detection against the height-map crop boundary for all 4 tracks: does the first extracted thermal frame's `x_mm_center` land close to 20mm and the last close to 100mm for every track, or does the laser-on/off heuristic drift for any one of them (see Pitfall 9)?

**Warning signs:**
- Width/boundary curves show a sharp discontinuity or unusually high variance in the first/last 1-2mm of the window compared to the interior.
- Thermal `x_mm_center` range for a track doesn't land close to `[20, 100]` when checked numerically.

**Phase to address:**
Target-extraction and dataset-alignment phases — a numeric sanity check (each track's thermal and height-map `x` ranges both ≈[20,100]) should be a hard assertion in the alignment code, run for all 4 tracks before the phase is marked done.

---

### Pitfall 8: Overconfident uncertainty calibration from too few held-out tracks

**What goes wrong:**
With only 4 tracks and a mandatory leave-one-track-out protocol, any calibration statistic (coverage, PICP, CRPS, log-likelihood) is ultimately estimated from **3-4 independent experimental units**, however many spatial positions each contains. Because within-track positions are spatially autocorrelated (Pitfall 2), the hundreds of positions per track do not behave like hundreds of independent draws for calibration purposes — the *effective* sample size for "is my uncertainty well-calibrated" is closer to 3-4 than to "hundreds of x positions." Reporting a single global coverage number (e.g., "89% of true widths fall inside the 90% interval") from one held-out track can look statistically convincing while actually being a high-variance, low-confidence estimate — precisely the failure mode the broader small-N cross-validation literature warns about: with small data, CV/calibration scores have too much variance to support strong claims, and traditional CV methods tend toward overconfident model/uncertainty selection ([Limitations of Bayesian LOO-CV for model selection](https://pmc.ncbi.nlm.nih.gov/articles/PMC6400414/); calibration of deep ensembles requires care in small-data regimes and calibration curves can be far from perfect where little data was available to inform them).

**Why it happens:**
Standard UQ tooling (conformal prediction, temperature scaling, PICP/CRPS reporting) is built assuming i.i.d. calibration/test samples and enough of them to estimate a coverage curve tightly; none of that holds here, but the tooling doesn't warn you.

**How to avoid:**
- Report calibration **per held-out track**, not just pooled/averaged across the (at most 4) leave-one-track-out folds — show the spread across folds explicitly rather than one aggregate number, and be honest in the report that N=4 tracks means wide uncertainty on the uncertainty estimate itself.
- Never tune calibration hyperparameters (temperature-scaling factor, conformal quantile, MC-dropout rate) on the same track being used as the final reported test fold — this reintroduces the same "spatial-correlation leakage" logic to the calibration step and produces circular, overconfident calibration.
- Prefer reporting calibration **qualitatively with visuals** (predicted mean ± band overlaid on true measured width curve, for the full held-out track) in addition to any single scalar metric — this is more honest about where uncertainty is well- vs. poorly-behaved (e.g., near track 21's data gaps) than a single PICP number, and plays directly to the organizer's stated criterion of "calibration and usefulness of predicted uncertainty."
- If time allows, evaluate calibration under a second, different held-out track (not just track 21) to see whether the calibration behavior is consistent — a single held-out track's calibration result is a single data point about your uncertainty model's quality, and should be treated as anecdotal, not conclusive.

**Warning signs:**
- A single tidy calibration number (e.g., "92% coverage, well calibrated!") in the report is not accompanied by a per-position or per-track breakdown.
- Calibration hyperparameters were fit or eyeballed using the same track later reported as the "held-out" evaluation.

**Phase to address:**
Evaluation-metrics phase — build the calibration reporting method (per-fold breakdown + visual bands) alongside the point-accuracy metric from the start, not as a bolt-on after the model is "done."

---

### Pitfall 9: Silent thermal-window misalignment specifically on the low-power (held-out) track

**What goes wrong:**
`detect_laser_on_interval` (`src/nsf_fmrg_data.py:100-111`) identifies the laser-on segment using a percentile-based frame-intensity score and a MAD/range-based threshold, then `extract_final_thermal_frames` takes the last `EXTRACTED_THERMAL_FRAMES` before the detected shutoff as the 20-100mm window. This heuristic depends on the melt pool producing a strong, clearly-separated intensity signature relative to the "laser off" baseline. Track 21 (200W) has both the smallest expected melt pool (lowest laser power) and the least-complete/most problematic post-process measurement of the 4 tracks — it is plausible (though not yet empirically confirmed in this codebase) that the same intensity-based on/off heuristic is *least* reliable exactly on this track, because a smaller/cooler melt pool produces a smaller signal-to-baseline gap. If the detected shutoff index is off by even a handful of frames on track 21, the entire extracted thermal window is shifted relative to true 20-100mm physical position on precisely the track used for final held-out evaluation — and because the shift is systematic (not random), it wouldn't show up as scattered noise, it would show up as a consistent phase offset between thermal and height-map/SEM coordinates for that one track, silently degrading the "leave-track-21-out" test score in a way that looks like "the model just doesn't generalize" rather than "the alignment for this track is wrong."

**Why it happens:**
The laser-on/off detection heuristic was tuned to work generically across tracks, but its two threshold branches (a range-based threshold and a MAD-based threshold, combined via `max()`) were not verified per-track against ground truth (e.g., against the physically known 100mm-mark or against the height map's independently-computed window). Nothing in the current pipeline cross-validates the thermal-detected window against the height-map crop.

**How to avoid:**
- For all 4 tracks, but *especially* track 21, plot `thermal_frame_score` alongside the detected `on_start`/`on_stop`/`threshold` and visually confirm the detected transition looks correct (a clean step, not a borderline call sitting near threshold noise).
- Cross-check that the thermal-derived `x_mm_center` range and the height-map-derived `x_actual_mm` range agree (both should span ≈20-100mm) for every track — build this as an automated assertion, not just a one-time eyeball check, since it must hold for the final leave-track-21-out run too.
- If track 21's detection looks borderline, consider a track-specific manual override (e.g., manually specify the shutoff frame index based on visual inspection) rather than trusting the generic heuristic blindly on the one track where a silent misalignment would be most costly to detect (since it's the whole team's evaluation number).

**Warning signs:**
- Track 21's detected `threshold` in `detect_laser_on_interval` sits close to either the range-based or MAD-based branch value rather than clearly dominated by one (a sign the detection was a close call).
- Any systematic phase-like offset between thermal-predicted geometry and true measured geometry specifically on track 21, that isn't present on the 3 training tracks.

**Phase to address:**
Dataset-alignment phase, before the cross-track validation harness is trusted — this is exactly the kind of phase PROJECT.md and organizer guidance flag as needing "deeper research"/extra scrutiny, precisely because track 21 is simultaneously the lowest-power, least-complete-data, *and* designated held-out track — three independent reasons for it to be the least reliable link in the alignment chain, combined into the one track the whole competition score depends on.

---

### Pitfall 10: Cross-sensor orientation/resolution mismatches beyond thermal

**What goes wrong:**
Three sensors, three independent orientation/scale conventions, reconciled by three separately-written code paths with no shared cross-check:
- **Thermal:** 400×400px @ ~14µm/px, native per-frame local coordinates, converted to physical `x` via frame-index arithmetic assuming constant 10mm/s scan speed and exactly 50fps.
- **SEM:** stored as per-track tiles in ascending file order representing decreasing physical `x` (tile 01 = 100mm side, highest tile number = 20mm side); the organizer-confirmed correct procedure is to stitch tiles in *ascending* file order using unmodified (unflipped/unrotated) tiles, and only flip the *entire completed mosaic* horizontally afterward. Reversing that order (e.g., flipping tiles individually before stitching, or stitching in descending order) silently produces a plausible-looking but incorrectly-aligned mosaic — every SEM patch would appear to show *some* substrate texture, so a wrong-orientation bug would not visually announce itself the way a crash would.
- **Height map:** Wyko `.ASC`, raw local `x=0` = physical 100mm side, reoriented via `x_actual_raw = 100.0 - x_local` and re-sorted (`load_wyko_asc`, `src/nsf_fmrg_data.py:160-202`); pixel size is read from the file header but **silently falls back to a hardcoded default (`0.003982` mm) if the `pixel_size` header token isn't found** for a given file — if any one track's ASC header uses a slightly different label or format than expected, that track's entire x/y coordinate grid is silently computed using the wrong physical scale, without any error being raised.

Because each modality's alignment is independently implemented and there is no automated cross-modality consistency check (e.g., overlaying the thermal-detected melt-pool centerline against the height-map track centerline at matching `x`, for all 4 tracks), a bug in any one of the three conventions produces a silent, confidently-wrong dataset rather than a crash.

**Why it happens:**
Each sensor's data format is genuinely different (image tiles vs. ASCII grid vs. video cube) and was necessarily hand-written per-modality; without an explicit joint sanity-check step, "does the code run without erroring" is mistaken for "the alignment is correct."

**How to avoid:**
- Add one mandatory cross-modality visual QA step per track (all 4, not just one representative track): overlay the height-map-derived track centerline/width envelope with the SEM mosaic (post-mask) and, separately, with a summary thermal statistic (e.g., peak intensity per position) — all plotted against the same physical `x` axis — and visually confirm they line up (e.g., wider SEM heat-affected-zone bands roughly coincide with wider extracted track width; thermal peak intensity roughly tracks laser power across tracks).
- For the height-map pixel-size fallback specifically: log a loud warning (not a silent default) whenever `pixel_size_mm` is not found in a given file's header, and manually confirm the header parsing succeeded for all 4 `.ASC` files before trusting any extracted target.
- Treat the organizer's SEM stitch-then-flip order as a literal, testable procedure — write a one-track unit check confirming that after stitching+flipping, the leftmost mosaic pixel corresponds to the lowest tile number's *far* edge, matching the README's stated post-flip tile order (`Plain_SEM_8_13, ..., Plain_SEM_8_01` left to right).

**Warning signs:**
- No visual side-by-side of all three modalities at matching `x` exists anywhere in the codebase/notebooks (currently true — this is a gap, not yet built).
- SEM-derived features (once masked) correlate poorly or in an unexpected direction with laser power/track identity, where basic physical intuition (e.g., higher power → different heat-affected zone) would predict some relationship.

**Phase to address:**
Dataset-alignment phase — build the tri-modal visual QA overlay as a required, checked deliverable of this phase (not an optional nice-to-have), for all 4 tracks, before any modeling phase begins.

---

### Pitfall 11: Over-investing in model/architecture complexity before the evaluation harness is trustworthy

**What goes wrong:**
Under an 8-day deadline it's tempting to jump straight to an elaborate model (multimodal fusion, deep video architectures, ensembles) because that's the "interesting" and "impressive" part of the project. But if the leave-one-track-out harness, target extraction, or cross-sensor alignment has any of Pitfalls 1-10 baked in, every hour spent tuning model architecture is spent optimizing against a broken yardstick — and the mistake is typically only discovered once results are (surprisingly) too good or (surprisingly) don't transfer, often with only 1-2 days left before the deadline to re-derive targets, fix alignment, and retrain.

**Why it happens:**
Model architecture work feels like "real progress" and produces visible artifacts (loss curves, predictions) quickly, while validating the harness (does leave-track-21-out actually exclude all track-21 data everywhere in the pipeline? does the width target look physically sane on all 4 tracks? are the three modalities aligned?) feels like unglamorous plumbing — but per PROJECT.md's own stated priority, "a complete simple pipeline beats an incomplete ambitious one," and per the organizer's evaluation criteria, all four graded axes (width/boundary error, spatial-variation preservation, geometry agreement, calibration) hinge entirely on the target and the split being correct, not on model sophistication.

**How to avoid:**
- Sequence the 8-day sprint so that target extraction, alignment, and the leave-one-track-out harness are locked and validated (visually, on all 4 tracks, including the specific checks in Pitfalls 6, 7, 9, 10) *before* any model beyond the simplest possible baseline (e.g., linear regression or shallow MLP on hand-crafted thermal summary statistics) is trained.
- Use that trivial baseline explicitly as a harness-validation tool: if a dead-simple model produces implausible results (e.g., near-perfect accuracy, or wildly discontinuous per-track scores), that is a signal to re-examine the harness, not to "fix" it by making the model more complex.
- Timebox architecture experimentation explicitly (e.g., no more than 2 of the 8 days) and treat any additional modeling sophistication (SEM fusion, ensembles, elaborate UQ) as stretch scope only reachable once the thermal-only baseline, evaluation, and packaging are already complete and committed — mirroring PROJECT.md's own explicit priority ordering.

**Warning signs:**
- Multiple days spent iterating on model architecture with no dedicated day/session having been spent specifically re-validating the target extraction or alignment against all 4 tracks.
- Suspiciously good early results with no cross-check against Pitfalls 1-5 (leakage) or 9-10 (alignment).

**Phase to address:**
Applies across all phases as a *sequencing* constraint: target extraction → alignment/QA → validation harness must each be independently validated before the model-training phase is allowed to begin; the roadmap should encode this as a hard phase-ordering dependency, not just a suggestion.

---

### Pitfall 12: No buffer time for producing the final executable/reproducible submission artifact

**What goes wrong:**
The competition requires "executable code" (a Jupyter notebook or GitHub repo link) that runs end-to-end — this project's own stated scope explicitly commits to that ("the pipeline must run end-to-end from raw data to figures/predictions, not just a describe-only report"). Teams that treat packaging/reproducibility as a same-day, last-minute task before the deadline commonly discover, too late, that: notebooks don't run top-to-bottom from a fresh clone (hidden state from out-of-order cell execution), file paths are hardcoded to one person's machine, `requirements.txt` is missing a dependency actually needed (e.g., `h5py`, needed only for the MAT v7.3 HDF5 fallback path, is not currently listed in the flat `requirements.txt`), or the repository accidentally still contains large raw data files that shouldn't be shared (see Pitfall 13).

**Why it happens:**
Packaging work (cleaning notebooks, pinning dependencies, testing a truly fresh-environment run, writing the couple of paragraphs on Generative-AI use required by the report template) is unglamorous and easy to underestimate; it's also inherently a *last* step, so any schedule slip upstream (model training running long, target extraction needing rework) directly eats into the only time block available for it.

**How to avoid:**
- Reserve a fixed, non-negotiable block (at minimum, the last full day of the 8, ideally with a dry run a day earlier) specifically for: fresh-clone/fresh-environment execution test, dependency pinning (`requirements.txt` completeness — confirm `h5py` is listed if the HDF5 fallback path is exercised by any of the 4 tracks), removing debug/scratch cells, and confirming output figures regenerate identically.
- Do this dry run *before* the final day, not on it — a same-day discovery of a broken fresh-clone run leaves no recovery time.
- Track this as an explicit roadmap phase/deliverable ("submission packaging"), not an implicit expectation folded into the modeling phase.

**Warning signs:**
- No one has run the full pipeline in a brand-new environment/clone since the model code was last changed.
- `requirements.txt` still reflects only the original starter-code dependencies (numpy, scipy, matplotlib, pillow, pandas) despite new modeling dependencies (e.g., a DL framework, `h5py`) having been added along the way.

**Phase to address:**
Dedicated submission-packaging phase, scheduled with fixed buffer near (but not on) the final day.

---

### Pitfall 13: Accidentally exposing competition-restricted raw data via a public submission repo

**What goes wrong:**
The submission format allows "a link to a GitHub repository" as the executable-code artifact. The dataset is explicitly restricted-use per `DATA_USE_LICENSE.md` — "sharing with non-participants" is prohibited. If the team's working repo (which already has `data/raw/` populated locally for development) is pushed to a public GitHub repo, or if a public repo's history ever contained the raw thermal `.mat`/SEM `.png`/height-map `.ASC` files, that would violate the data-use terms regardless of intent, and is a compliance risk distinct from (but easy to conflate with) ordinary "don't commit large binaries" hygiene.

**Why it happens:**
`.gitkeep` placeholders make it easy to forget that `data/raw/` is populated locally as soon as development starts, and a routine `git add -A` or making a private dev repo public near the deadline can pull that data along without anyone noticing, especially under time pressure.

**How to avoid:**
- Keep `data/raw/` (and any derived caches containing raw pixel/height data) gitignored throughout, and verify this explicitly right before choosing the GitHub-link submission path (`git log --all -- data/raw` should be empty).
- If submitting via GitHub link, keep the repository private and grant access only as required by the submission mechanism, or prefer submitting a self-contained Jupyter notebook instead if repo-visibility requirements are unclear.

**Warning signs:**
- Repo size unexpectedly large, or `git log -- data/raw` shows non-empty history.

**Phase to address:**
Submission-packaging phase — add as an explicit pre-flight checklist item.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|------------------|
| Hand-tuned absolute-height threshold for track edge, validated on one track only | Fast target extraction, unblocks modeling sooner | Definition breaks or silently distorts for other 3 tracks/powers; invalidates cross-track comparison | Never for the final target — only as a throwaway first pass to unblock early pipeline wiring, must be replaced before model training |
| Fixed global normalization computed once over all 4 tracks | Simpler preprocessing code | Preprocessing leakage into leave-one-track-out folds (Pitfall 5) | Never — refit per-fold, this is cheap to do correctly from day one |
| Keeping the `find_track_file` substring fallback unmodified | Saves 10 minutes of hardening now | Silent cross-track file mismatch risk (Pitfall 4), invisible until output looks "off" | Acceptable only after a one-time manual verification confirms current 4 filenames don't collide; document the check, don't just skip it |
| Skipping the tri-modal visual alignment overlay to save a day | Faster path to a trained model | Any orientation/scale bug in thermal, SEM, or height-map alignment goes undetected until final scoring (Pitfall 9, 10) | Never — this is a cheap (few hours), high-leverage check relative to its downside |
| Deferring uncertainty calibration reporting until the very end | More time for point-accuracy model tuning | Miscalibrated/overconfident UQ discovered too late to fix before deadline; UQ is one of the four explicit organizer evaluation axes | Acceptable only if a placeholder calibration check runs continuously from the first working model onward, even if crude |

## Integration Gotchas (cross-sensor alignment)

| Sensor pairing | Common Mistake | Correct Approach |
|-----------------|------------------|--------------------|
| Thermal ↔ height map | Trusting the laser-on/off intensity heuristic blindly for all tracks, especially low-power track 21 | Visually verify detected on/off transition per track; cross-check thermal `x_mm_center` range against height-map `x_actual_mm` range for all 4 tracks |
| SEM ↔ height map | Flipping/rotating individual SEM tiles before stitching, or stitching in the wrong file order | Stitch unmodified tiles in ascending file-number order first, flip only the completed mosaic horizontally afterward (organizer-confirmed procedure) |
| Height map `.ASC` header ↔ physical scale | Silently accepting the hardcoded pixel-size fallback (`0.003982` mm) when a file's header token isn't recognized | Log/warn loudly on fallback use; manually confirm header parsing succeeded (`x_size`, `y_size`, `pixel_size_mm` all present) for every one of the 4 files |
| All three modalities ↔ shared 20-100mm window | Assuming the crop is "just a slice," not accounting for boundary/edge effects in windowed calculations | Numerically assert each track's per-modality x-range spans ≈[20,100]mm; treat the first/last few mm as a special case in extraction/smoothing code |

## "Looks Done But Isn't" Checklist

- [ ] **Target extraction:** Looks done once it runs on one track without erroring — verify it was visually validated against *all 4* tracks, including track 21's gap-heavy regions, with a relative (not absolute) edge-detection criterion.
- [ ] **Leave-one-track-out harness:** Looks done once cross-validation code exists — verify no shuffle/random-split fallback path exists anywhere in the modeling or hyperparameter-tuning code, and that any inner (nested) validation also respects whole-track holdout.
- [ ] **SEM masking:** Looks done once a mask shape is defined — verify it was visually overlaid against the stitched mosaic *and* the height-map track outline for all 4 tracks, sized against the widest (400W) track, not tuned per track.
- [ ] **Multimodal alignment:** Looks done once loaders run without exceptions — verify a joint visual QA overlay (thermal summary + SEM (masked) + height-map width envelope, common x-axis) exists for all 4 tracks, not just one.
- [ ] **Uncertainty calibration:** Looks done once a single PICP/coverage number is reported — verify it's broken out per held-out track/fold, and that no calibration hyperparameter was tuned on the same track used as the final reported test fold.
- [ ] **Submission packaging:** Looks done once the notebook runs on the developer's machine — verify a genuinely fresh clone/fresh environment run succeeds, `requirements.txt` includes every dependency actually exercised (including `h5py` if any track needs the HDF5 fallback), and `data/raw/` is confirmed absent from git history.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|----------------|------------------|
| SEM target leakage discovered late | MEDIUM | Since SEM fusion is stretch scope, simply drop the SEM-fused variant and ship the thermal-only baseline (already the recommended core deliverable) — low cost precisely because the project is already sequenced this way |
| Spatial-correlation leakage in validation harness | HIGH if discovered near deadline | Re-run all reported metrics through a corrected leave-one-track-out harness; if time is short, prioritize re-validating and re-reporting metrics over re-training a better model — a correct metric on an existing model beats an incorrect metric on a better one |
| Track file mismatch (Pitfall 4) | LOW-MEDIUM | 10-minute manual filename audit across the 4 tracks × 3 modalities; fix `find_track_file` regex/assertions; re-run the affected phase only (not necessarily full re-train, if caught before model training) |
| Thermal window misalignment on track 21 | HIGH if discovered post-training | Requires re-extracting thermal frames for track 21 with a corrected/manual shutoff index and re-scoring the held-out evaluation only (training on tracks 8/10/14 need not be redone unless they trained with track-21-referenced normalization statistics — see Pitfall 5) |
| Miscalibrated UQ discovered late | MEDIUM | Report calibration honestly with the caveat noted (N=4 tracks, high variance) rather than fabricating a falsely tight number; a transparent limitations discussion is explicitly welcomed by the report rubric ("limitations and uncertainties") |
| Submission packaging broken close to deadline | HIGH (time is the scarce resource here) | Fall back to a single self-contained notebook (simpler reproducibility surface than a full repo) if a clean repo run cannot be verified in time |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|----------------|
| SEM target leakage (1) | SEM stitching + masking phase (stretch) | Visual mask/mosaic/track-outline overlay for all 4 tracks shows zero overlap |
| Spatial-correlation leakage (2) | Cross-track validation harness phase | Code review confirms no position-level shuffle-split path exists anywhere, including nested/inner validation |
| Track identity as leaky feature (3) | Feature engineering / dataset construction phase | Ablation: metadata-only model vs. thermal-only model, both leave-one-track-out, results documented |
| `find_track_file` mismatch (4) | Data-loading phase | Manual filename audit across 4 tracks × 3 modalities logged before target extraction begins |
| Preprocessing/normalization leakage (5) | Target extraction + validation harness phases | Per-fold-only statistics fitting checked in code review |
| Noisy/inconsistent width extraction (6) | Target extraction phase | Visual validation of extracted width/boundary curves against all 4 tracks, incl. track 21 gaps |
| Window boundary edge effects (7) | Target extraction + alignment phases | Numeric assertion: each track's thermal/height-map x-range ≈[20,100]mm; edge region flagged in report |
| Overconfident UQ calibration (8) | Evaluation metrics phase | Per-fold calibration breakdown reported, not just a single pooled number |
| Silent thermal misalignment on track 21 (9) | Dataset alignment phase | Visual on/off detection plot + cross-modality x-range check specifically for track 21 |
| Cross-sensor orientation/scale mismatch (10) | Dataset alignment phase | Tri-modal visual QA overlay built and checked for all 4 tracks |
| Over-investing in model complexity early (11) | Sprint/roadmap sequencing (cross-phase) | Roadmap enforces target-extraction → alignment → harness validation before model-training phase starts |
| No submission-packaging buffer (12) | Submission packaging phase | Fresh-clone/fresh-environment dry run completed at least one day before deadline |
| Raw data exposure via public repo (13) | Submission packaging phase | `git log --all -- data/raw` confirmed empty before choosing GitHub-link submission path |

## Sources

- [Limitations of Bayesian Leave-One-Out Cross-Validation for Model Selection — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6400414/) (MEDIUM — peer-reviewed, general CV/model-selection variance argument, not domain-specific)
- [scikit-learn: LeaveOneGroupOut / Cross-validation docs](https://scikit-learn.org/stable/modules/cross_validation.html) (HIGH — official library documentation on group-based CV semantics)
- [Fair train-test split in machine learning: Mitigating spatial autocorrelation — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0920410521015023) (MEDIUM — peer-reviewed, directly on spatial-autocorrelation leakage)
- [Spatial cross-validation using scikit-learn — Towards Data Science](https://towardsdatascience.com/spatial-cross-validation-using-scikit-learn-74cb8ffe0ab9/) (LOW-MEDIUM — practitioner blog, corroborates peer-reviewed source above)
- [Quantifying Deep Learning Model Uncertainty in Conformal Prediction](https://arxiv.org/html/2306.00876v2) (MEDIUM — preprint, general small-data calibration caveats)
- [Calibrating ensembles for scalable uncertainty quantification — ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0010482523005619) (MEDIUM — peer-reviewed, calibration-in-small-data-regime nuance)
- [Roughness measurements across topographically varied additively manufactured metal surfaces — ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214860423001537) (MEDIUM — peer-reviewed, AM-specific profilometry edge-effect practice: maintaining a boundary margin from build edges)
- Kaggle community discussion on leaderboard overfitting and beginner mistakes (various, incl. [Yanir Seroussi: How to (almost) win Kaggle competitions](https://yanirseroussi.com/2014/08/24/how-to-almost-win-kaggle-competitions/)) (LOW-MEDIUM — practitioner community consensus, not peer-reviewed, used only for general sprint-discipline framing)
- Direct source inspection of this repository's own preprocessing library: `src/nsf_fmrg_data.py` (find_track_file, `_loadmat_any`, `find_thermal_array`, `detect_laser_on_interval`, `extract_final_thermal_frames`, `load_wyko_asc`, `robust_plane_detrend`) — (HIGH confidence; codebase-grounded pitfalls 4, 6 (detrend specifics), 9, 10 are derived directly from reading this code, not from web sources)
- `README.md` (this repo) — organizer clarifications on SEM stitching/masking, evaluation framework, validation strategy, track↔power mapping (HIGH — primary/authoritative source, direct from competition organizers)
- `DATA_USE_LICENSE.md` (this repo) — data-restriction terms underlying Pitfall 13 (HIGH — primary source)

---
*Pitfalls research for: Thermal-to-geometry prediction (DED laser manufacturing), NSF FMRG Data Challenge*
*Researched: 2026-07-19*
