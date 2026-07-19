# NSF Future Manufacturing Data Challenge

### Predicting Laser Track Variation from Thermal Imaging

This repository contains starter code, notebooks, documentation, and paper files for the **NSF Future Manufacturing Data Challenge**.

In modern manufacturing, the quality of a component is often shaped by real-time events during production. With advanced cameras and sensors, we can monitor these events as they unfold. This challenge explores whether we can predict the final quality of manufactured parts by watching them as they are made — specifically, connecting **thermal images** recorded during a laser-etching (directed energy deposition) process to the **final shape and variation** of the resulting laser track.

The raw multimodal dataset is hosted on Zenodo:
**Dataset DOI:** [10.5281/zenodo.21285367](https://doi.org/10.5281/zenodo.21285367)
The data is also available in the `./dataset_zenodo/` folder.

This competition and associated material are based upon work supported by the National Science Foundation under Grant Number **FMRG-2328395**. It is organized by the **Texas A&M Institute of Data Science** and the **Department of Engineering Technology & Industrial Distribution at Texas A&M University**.

## Competition at a glance

This is a **two-week data challenge**. Participants receive a challenge prompt and a dataset, conduct their analysis, write a report, and submit it by the deadline. Selected finalists are invited to present to a panel of judges during a virtual Final Event.

| Item | Detail |
|------|--------|
| **Start date** | July 13, 2026 |
| **Submission deadline** | July 27, 2026 |
| **Finalist presentations & awarding event** | July 31, 2026, 5:00–7:00 pm Central Time (virtual) |
| **Format** | Team-based; submit a report, executable code, and a slide deck |
| **Finalists** | Judges select 3–5 finalist teams; each presents for 10 minutes (including Q&A) |
| **Organizers** | Texas A&M Institute of Data Science; Dept. of Engineering Technology & Industrial Distribution, Texas A&M University |
| **Funding** | NSF Grant Number FMRG-2328395 |

Submission link: https://tamu.qualtrics.com/jfe/form/SV_emSeErTTgRkWw3s?Q_CHL=gl&Q_DL=EMD_2gAbx5z26nWSQYC_emSeErTTgRkWw3s_CGC_9UIc7OKteuxR023&_g_=g

### Prizes

| Award | Amount |
|-------|--------|
| First Place | $1,000 |
| Second Place | $500 |
| Third Place | $300 |
| Best Presentation (special prize) | $100 |
| Most Innovative Approach (special prize) | $100 |

## Dataset overview

The challenge focuses on predicting **probabilistic local geometric variation** of single laser tracks in directed energy deposition (DED) using multimodal data:

- in-situ thermal image sequences,
- SEM images of surrounding substrate morphology,
- Bruker/Wyko full-field height maps.

The central idea is to combine the **in-situ thermal history** of the laser–material interaction with the **local morphology of the substrate**, and to predict local geometry *and its uncertainty* along the scan path, rather than a single average value for the whole track.

### Experimental setup

![Experimental setup: Optomec MTS 500, Bruker ContourGT-K, and Zeiss EVO MA10](paper/figures/experimental_setup_optomec_bruker_zeiss.png)

The dataset was generated from single bead-on-plate laser scans on **stainless-steel 316L** substrates using an **Optomec LENS MTS 500** hybrid manufacturing platform. Post-process characterization was performed using a **Bruker ContourGT-K** white-light 3D optical profilometer (Bruker/Veeco height maps) and a **Zeiss EVO MA10** SEM system.

Each experiment creates a **100 mm long track**. The laser moves at a scan speed of **10 mm/s**, and the thermal camera records at **50 frames per second**, so each consecutive thermal frame corresponds to approximately **0.2 mm of laser travel**. Each thermal frame is **400 × 400 pixels** at a physical resolution of approximately **14 µm/pixel**, with the melt pool located near the center of the frame.

### Representative modalities

![Representative thermal, SEM, and height-map modalities](paper/figures/modality_examples_three_panel.png)

The thermal frames provide in-situ process information, the SEM tiles provide local substrate-morphology context, and the height maps provide the post-process geometry used to define local track descriptors such as width, boundary position, contour deviation, edge roughness, or related probabilistic targets. For every track, the analysis focuses on a shared physical interval from approximately **20 mm to 100 mm** along the scan direction.

### Track ↔ laser power mapping

Four laser powers were investigated at a fixed scan speed of 10 mm/s. The realized experiments correspond to track IDs 8, 10, 14, and 21:

| Laser power | Track ID | Notes |
|-------------|----------|-------|
| 400 W | 8 | — |
| 350 W | 10 | — |
| 300 W | 14 | — |
| 200 W | 21 | **Held out** — recommended test track; profilometry coverage is less complete |

> **Tip:** Once you start exploring the thermal data, higher laser power corresponds to a **bigger melt pool**, which provides a quick sanity check on the mapping above.

## Repository structure

```text
nsf-fmrg-data-challenge/
├── README.md
├── DATA_USE_LICENSE.md
├── CITATION.cff
├── requirements.txt
├── data/
│   └── raw/
│       ├── thermal/
│       │   └── .gitkeep
│       ├── sem/
│       │   ├── SEM_8/
│       │   │   └── PlainImages/
│       │   ├── SEM_10/
│       │   │   └── PlainImages/
│       │   ├── SEM_14/
│       │   │   └── PlainImages/
│       │   └── SEM_21/
│       │       └── PlainImages/
│       └── height_maps/
│           └── .gitkeep
├── notebooks/
│   ├── 01_starter_code_loading_and_visualization.ipynb
│   └── 02_starter_code_loading_and_visualization_standalone_colab.ipynb 
├── src/
│   └── nsf_fmrg_data.py
├── scripts/
│   └── run_thermal_video_export.py
├── paper/
│   ├── research_paper.md
│   └── figures/
│       ├── experimental_setup_optomec_bruker_zeiss.png
│       └── modality_examples_three_panel.png
└── processed_data/
    └── .gitkeep
```

## Data access

Upon the official start of the competition, registered teams are provided with **GitHub access to the competition dataset**. The raw data are hosted externally on Zenodo because the files are too large for regular GitHub upload. After downloading the Zenodo files, extract them into the repository using this layout:

```text
data/raw/thermal/
  Thermal_8.mat
  Thermal_10.mat
  Thermal_14.mat
  Thermal_21.mat

data/raw/sem/
  SEM_8/PlainImages/
  SEM_10/PlainImages/
  SEM_14/PlainImages/
  SEM_21/PlainImages/

data/raw/height_maps/
  Heightmap_8.ASC
  Heightmap_10.ASC
  Heightmap_14.ASC
  Heightmap_21.ASC
```

The `.gitkeep` files are placeholders that keep the empty folders visible on GitHub. They can remain in the folders after the raw data are added locally.

**Data usage:** The dataset is provided for the sole and exclusive purpose of participating in this competition. Using the dataset for any purpose outside of the competition — including personal projects, other academic work, commercial applications, or sharing with non-participants — is strictly prohibited. The competition does **not** provide access to any computational or other resources beyond the dataset.

## Challenge task

**Challenge prompt:** Given a sequence of thermal images recorded during laser scanning, develop a model that predicts the **local geometric variation** of the final laser track.

> **Organizer clarification (Discord, July 17, 2026):** The task, alignment, masking, and evaluation guidance below incorporates answers provided by the competition organizers in the competition Discord.

Participants should treat the laser track as a **spatially varying feature** rather than a perfectly uniform line. Even when process settings are held constant, a track's width, left/right boundaries, surface contour, and edge waviness vary continuously along the scan direction. A single global width value hides these variations. The objective is to learn how patterns in the thermal images — especially around the moving melt pool — relate to the final track geometry measured after processing.

At minimum, a submission should describe either the local track width
`w_i(x) = y_upper,i(x) - y_lower,i(x)` or the corresponding upper/lower (left/right) boundary functions. Here, `x` is a **spatial coordinate along the scan direction**, not time, so `w_i(x)` is a spatial sequence rather than a time series. Participants do not need to predict every possible geometry descriptor. Beyond the minimum output, representations may include any combination of:

- left/right boundary position,
- centerline displacement,
- contour deviation,
- edge roughness / waviness,
- other vector-valued or probabilistic geometry descriptors.

Width captures changes in track size. Separate boundary functions can additionally capture lateral shifting, asymmetry, and edge variation. Participants may use any physically meaningful internal representation, provided it is extracted consistently from the height maps and can be compared with measured local geometry.

### Three guiding principles

1. **Predict locally** — predict local geometry `g_i(x)` at each position `x` along the 20–100 mm analysis window, not one global number.
2. **Quantify uncertainty** — output a probability distribution (expected prediction *and* uncertainty), and aim for calibrated uncertainty.
3. **Preserve physical alignment** — keep thermal, SEM, and height-map measurements aligned to the same physical coordinate.

### Sources of variation

Final track variation comes from two sources, and a strong submission tries to distinguish them:

- **Process-driven variation** — reflected in the thermal history: melt pool size, shape, intensity, and cooling behavior.
- **Substrate-driven variation** — valleys, ridges, and local surface/subsurface irregularities already present in the plate that influence how the molten region spreads and resolidifies.

### Main goals

1. **Extract thermal descriptors of the moving melt pool** — e.g. melt pool size, shape, temperature distribution, intensity gradients, asymmetry, cooling-tail behavior, frame-to-frame changes, or learned ML features.
2. **Represent laser track variation as a spatial signal** — a quantity that changes along the scan direction (local width, boundary position, boundary fluctuation, edge roughness, waviness, local contour deviation), not a single average width.
3. **Predict local track geometry from thermal history** — use one thermal frame or a short sequence of consecutive frames to predict the corresponding local track segment (frame-level, short spatial windows, or longer segments).
4. **Account for multiple sources of variation** — identify or quantify process- vs. substrate-driven variation where possible.
5. **Provide interpretable links** — explain which thermal features are most strongly related to track formation, local geometric variation, or irregular boundaries. Accuracy matters, but so does insight.

### Modeling framework (input → output pair)

Because the melt pool moves continuously, a single physical location `x_j` is visible in several neighboring thermal frames as the melt pool approaches, passes over, and moves away. One complete model input/output pair is therefore defined as:

- **Thermal input `T_ij`** — a short *video tensor* of `2K + 1` consecutive frames centered on the frame where the melt pool is at `x_j`. Adjacent active frames are ≈ 0.2 mm apart, so the tensor captures heating, melt-pool behavior, and cooling around the same physical location.
- **SEM input** — the local substrate-morphology patch covering `x_j`, with the **processed track region masked/excluded** to prevent target leakage (otherwise the model could directly observe the final geometry).
- **Metadata** — physical coordinate `x`, laser power, and track identity `i`. You may also derive additional parameters such as **energy density**.
- **Output** — at minimum, local width `w_i(x)` or the corresponding boundary functions; probabilistic models may additionally return a distribution over local geometry `g_i(x)` (e.g. a mean width curve with an uncertainty band across the 20–100 mm interval).

## Physical coordinate conventions

Because the modalities come from different sensors and file formats and are **not stored in the same direction or indexing convention**, aligning them in physical space is a key part of the challenge.

### Thermal data

- File type: `.mat`
- Native frame size: `400 × 400`
- Pixel size: approximately `14 µm/pixel`
- Field of view: approximately `5.6 mm × 5.6 mm`
- Frame rate: `50 fps`
- Scan speed: `10 mm/s`
- Travel per thermal frame: `0.2 mm/frame`
- The 20–100 mm analysis window contains approximately `400` thermal frames.
- Thermal files include frames before laser turn-on and after laser shutoff. The processing notebook detects laser shutoff and extracts the previous 400 frames.

### SEM data

- File type: `.png`
- Images are stored as per-track tiles in `PlainImages`.
- Tile 01 corresponds to the physical 100 mm side.
- The highest-numbered tile corresponds to the physical 20 mm side.
- **Tile naming convention:** a file such as `Plain_SEM_8_13` encodes track ID (`8`) and image number (`13`).
- The participant starter notebook reads SEM tiles but does not stitch them.

#### Organizer-confirmed SEM stitching and alignment

To align an SEM mosaic with the height map while preserving the vertical orientation:

1. Stitch the unmodified SEM tiles in ascending file order (`Plain_SEM_8_01`, `Plain_SEM_8_02`, ..., `Plain_SEM_8_13` for track 8), using their actual overlapping image regions. Approximately **5% overlap** is a suggested starting point.
2. Do **not** flip or rotate individual tiles.
3. After stitching the complete mosaic, flip the entire mosaic horizontally:

   ```python
   sem_mosaic_aligned = np.fliplr(sem_mosaic)
   ```

After the flip, track 8 runs left-to-right as `Plain_SEM_8_13`, `Plain_SEM_8_12`, ..., `Plain_SEM_8_01`, matching the height map's returned 20–100 mm direction. A horizontal flip reverses only the scan-direction axis, so the top/bottom orientation is preserved.

#### SEM masking requirements

SEM input is intended to describe the **surrounding substrate morphology**—valleys, ridges, and other surface features that may affect local track formation. The processed laser-track region must be completely excluded so the model cannot infer the target from the final track appearance.

The organizers suggested a masking scheme that:

- is centered on the nominal laser scan path,
- is defined in physical coordinates,
- applies the same rule to every track,
- covers the entire processed track region, and
- includes a small safety margin so no part of the final track enters the SEM input.

The clarification does not prescribe straight versus curved mask boundaries or one fixed mask size. Whatever construction is chosen should satisfy the exclusion requirements above and be documented so it can be applied reproducibly. All teams will be assessed under the same standardized evaluation framework.

### Bruker/Wyko height maps

- File type: Wyko ASCII `.ASC`
- `x` and `y` values are stored in millimeters.
- `z` values are stored in nanometers and converted to millimeters or micrometers in the code.
- Raw ASC local `x = 0` corresponds to the physical 100 mm side.
- The loader sorts columns so returned height maps increase from 20 mm to 100 mm in actual part coordinates.
- These profilometer-derived measurements serve as the **ground truth** for model training and evaluation.

> **Ground-truth clarification:** The measured height map itself is the ground-truth spatial measurement. The organizers do not provide a separate label file or an official function for extracting width or boundaries. Participants must define and consistently apply their own post-processing method, justify why the resulting representation is physically meaningful, and document it for reproducibility.

## Recommended workflow

A recommended six-stage processing and modeling workflow:

1. **Load** the thermal `.mat` files, SEM `.png` images, and ASCII height maps.
2. **Convert units consistently** — pixel positions to millimeters, and height values from nanometers to micrometers or millimeters.
3. **Correct coordinate direction and crop** the shared 20–100 mm interval.
4. **Construct aligned training pairs** by associating each thermal sequence and masked SEM morphology with the geometry target and the `x` coordinate.
5. **Train** either a single-modality or a multi-modal probabilistic model.
6. **Evaluate** on a held-out track using both prediction accuracy and uncertainty quality.

Throughout, **preventing SEM target leakage** (masking the processed track) is essential.

## Validation strategy and quantitative evaluation

Because the dataset contains only **four track conditions**, the validation strategy matters. Randomly splitting neighboring coordinates from the same track into train/test sets produces overly optimistic results, since adjacent locations are spatially correlated (the model effectively sees almost the same region).

- **Use cross-track validation.** Exclude one complete track during training and use it only for testing.
- **Track 21 (200 W) is a useful conservative held-out case** — its profilometry coverage is less complete, which tests robustness to imperfect post-process measurement.

### Organizer-confirmed evaluation framework

Final ranking is **not** based only on the report and presentation. Predictions will be evaluated quantitatively against geometry derived from the measured height maps. Although teams may choose different models and internal representations, every submission will be assessed using the same standardized framework and criteria.

The quantitative evaluation will consider:

- error between predicted and measured local width or boundary functions,
- preservation of spatial variations along the track,
- overall agreement between predicted and measured track geometry, and
- for probabilistic models, the calibration and usefulness of predicted uncertainty.

The organizer clarification did not specify exact metric formulas or numerical weights. For internal model development, useful candidate metrics include:

- Mean absolute error (MAE) for local width,
- Boundary position error,
- Log-likelihood or Continuous Ranked Probability Score (CRPS) for probabilistic predictions,
- Calibration error and uncertainty-interval coverage.

These candidate metrics are development suggestions, not a claim that they are the final weighted ranking formula.

## Submission requirements

Teams submit all materials as a **single Zip file** through a **Qualtrics link emailed to participants** after the event launches. Multiple updates are allowed before the deadline, but **only the last submitted file is reviewed**, and **no late submissions are accepted**.

The Zip file must contain:

**1. Final report (PDF)** — maximum **3 pages**, minimum **10 pt Arial** font, **1-inch margins** all around. At minimum it should include:

- **Executive Summary** — summary of your analysis methodology, coding approach, and resulting insights.
- **Problem Formulation and Methodology** — your specific approach, including a description of any **Generative AI** used in the project.
- **Modeling and Outcomes** — models/predictions, limitations and uncertainties, and specifically:
  - predicted local track variation along the laser path,
  - predicted local track width and/or boundary positions,
  - track variation descriptors such as roughness, waviness, or local boundary variance,
  - quantitative comparison with profilometer-derived ground truth,
  - an uncertainty estimate for the predicted geometry, where applicable.
- **Conclusion** — a short interpretation of how thermal image behavior relates to final track variation.
- *(Optional)* **Visualizations** — with a description of what each conveys and why it is included.
- *(Optional)* **Appendix.**

**2. Executable code** — a Jupyter notebook or a link to a GitHub repository. Do **not** submit raw code. Reuse is OK, but you must acknowledge any external sources used.

**3. Presentation slide deck** — self-contained in a single PowerPoint file or similar format (e.g. PDF), describing the results of your work. Finalists have 10 minutes at the Final Event (including Q&A).

## Review / evaluation criteria

The quantitative portion of evaluation focuses on:

- accuracy of predicted local geometry,
- error in local width or boundary predictions,
- preservation of spatial track variations,
- overall agreement with measured height-map geometry,
- robustness across different laser powers,
- calibration and usefulness of uncertainty estimates for probabilistic submissions.

The report and presentation assess complementary qualitative criteria, including:

- physical justification of the chosen geometry representation,
- reproducibility and consistency of geometry extraction,
- interpretation of results,
- novelty of the approach,
- interpretability of thermal descriptors or learned features,
- ability to distinguish process-driven variation from substrate-driven variation.

The report and presentation support the judging process, but do not replace quantitative evaluation against the measured height maps.

The judges select **3–5 finalist teams** to present at the Final Event on July 31, 2026. The top three teams win the main prizes, and special prizes are awarded for **Best Presentation Design** and **Most Innovative Approach**.

## Notebooks

### Organizer/post-processing notebook

Use this notebook to check data, generate figures, extract thermal frames, and export thermal videos:

```text
notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb
```

This notebook is fully standalone and does **not** depend on `src/`.

### Participant starter notebook

Use this notebook as the clean starting point for participants:

```text
notebooks/01_starter_code_loading_and_visualization.ipynb
```

This notebook demonstrates:
- thermal loading and 20–100 mm extraction,
- SEM tile loading,
- Bruker/Wyko height-map loading,
- basic physical-coordinate visualization,
- optional display-only tilt inspection.

## Paper

The companion dataset paper PDF is included in:

```text
paper/2607.07965v1.pdf
```

or found here:

```text
https://arxiv.org/abs/2607.07965
```

## Installation

From the repository root:

```bash
python -m pip install -r requirements.txt
```

The notebooks are designed to run in Local System and/or Google Colab. For local use, a standard scientific Python environment with NumPy, SciPy, Matplotlib, Pillow, and Pandas is sufficient. Utilize uv to create, manage, and work with virtual environments.

## Citation

If you use this dataset or code outside the NSF Future Manufacturing Data Challenge, cite the dataset paper, this GitHub repository, and the Zenodo dataset DOI:

```bibtex
@dataset{hanchate2026nsffmrgdedchallengedata,
  title        = {NSF Future Manufacturing Data Challenge: A Multimodal DED Dataset for Probabilistic Local Geometry Prediction in Laser Tracks},
  author       = {Hanchate, Abhishek and Balhara, Himanshu and Bukkapatnam, Satish T. S.},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.21285367},
  url          = {https://doi.org/10.5281/zenodo.21285367},
  note         = {Dataset, code, and starter material for the NSF Future Manufacturing Data Challenge}
}
```

and/or 

```bibtex
@misc{hanchate2026nsffmrgdedchallenge,
  title          = {NSF Future Manufacturing Data Challenge: A Multimodal DED Dataset for Probabilistic Local Geometry Prediction in Laser Tracks},
  author         = {Hanchate, Abhishek and Balhara, Himanshu and Bukkapatnam, Satish T. S.},
  year           = {2026},
  eprint         = {2607.07965},
  archivePrefix  = {arXiv},
  primaryClass   = {physics.app-ph},
  url            = {https://arxiv.org/abs/2607.07965},
}
```

## License and data-use terms

See [`DATA_USE_LICENSE.md`](DATA_USE_LICENSE.md).

Challenge use is permitted for registered participants. The dataset is provided for the sole and exclusive purpose of participating in this competition; use for personal projects, other academic work, commercial applications, or sharing with non-participants is prohibited. Any use outside the NSF Future Manufacturing Data Challenge must cite the dataset paper, this repository, and the Zenodo dataset DOI.
