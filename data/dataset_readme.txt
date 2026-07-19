NSF Future Manufacturing Data Challenge Dataset

This dataset contains multimodal data for probabilistic local geometry prediction in single DED laser tracks. It supports the NSF Future Manufacturing Data Challenge and contains multimodal measurements for probabilistic local geometry prediction in single directed energy deposition (DED) laser tracks on SS316L substrates. The dataset includes in-situ thermal image sequences, SEM images of surrounding substrate morphology, and Bruker/Wyko full-field height maps. The common analysis window corresponds to physical part coordinates 20–100 mm. The dataset is intended for developing models that predict local track width, boundary position, contour deviation, edge roughness, or related probabilistic descriptors from process-driven and substrate-driven information.

Modalities:
1. Thermal image sequences from a Stratonics ThermaViz melt-pool sensor.
2. SEM images from a Zeiss EVO MA10 system.
3. Full-field height maps from a Bruker ContourGT-K white-light 3D optical profilometer.

Physical conventions:
- Common analysis window: 20–100 mm.
- Thermal frame size: 400 × 400 pixels.
- Thermal pixel size: approximately 14 µm/pixel.
- Thermal field of view: approximately 5.6 mm × 5.6 mm.
- Thermal frame rate: 50 fps.
- Scan speed: 10 mm/s.
- Consecutive thermal frames correspond to approximately 0.2 mm of laser travel.
- Bruker/Wyko ASC files store x and y in mm and z in nm.
- Raw ASC local x = 0 corresponds to the physical 100 mm side; starter code maps height maps to increasing 20–100 mm actual coordinate order.
- SEM tile 01 corresponds to the 100 mm side; the highest-numbered SEM tile corresponds to the 20 mm side.

Acknowledgment:
This competition and associated material are based upon work supported by the National Science Foundation under Grant Number FMRG-2328395.

Citation:
Please cite the companion dataset paper and GitHub repository for any use outside the NSF Future Manufacturing Data Challenge

APA style: Hanchate, A., Balhara, H.& Bukkapatnam, S. (2026). NSF Future Manufacturing Data Challenge: A Multimodal DED Dataset for Probabilistic Local Geometry Prediction in Laser Tracks [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.21285367

Harvard style: Hanchate, A., Balhara, H. and Bukkapatnam, S. (2026) “NSF Future Manufacturing Data Challenge: A Multimodal DED Dataset for Probabilistic Local Geometry Prediction in Laser Tracks”. Zenodo. Available at: https://doi.org/10.5281/zenodo.21285367.

MLA style: Hanchate, A., et al. “NSF Future Manufacturing Data Challenge: A Multimodal DED Dataset for Probabilistic Local Geometry Prediction in Laser Tracks”. Zenodo, 9 July 2026, https://doi.org/10.5281/zenodo.21285367.

IEEE style: [1]A. Hanchate, H. Balharaand S. Bukkapatnam, “NSF Future Manufacturing Data Challenge: A Multimodal DED Dataset for Probabilistic Local Geometry Prediction in Laser Tracks”. Zenodo, Jul. 09, 2026. doi: 10.5281/zenodo.21285367.