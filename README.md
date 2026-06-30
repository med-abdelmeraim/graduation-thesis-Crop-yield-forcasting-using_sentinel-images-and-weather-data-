# Deep Learning Approaches for Crop Yield Forecasting Using Sentinel-2 and Weather Data

This repository contains the code and experiments for my master's thesis:

> **Deep Learning Approaches for Crop Yield Forecasting Using Sentinel Images and Weather Data: Case Study on the CropNet Soybean Dataset**

We develop two complementary deep learning models for county-level soybean yield prediction under climate change:

- **GraphCrossFormer** – a compact, weather-only Transformer with a feature graph and SeasonMask phenological gating.
- **CNN-GRU (multi-modal)** – a model that fuses Sentinel-2 imagery and HRRR weather via gated fusion, spatial attention, and SeasonMask-modulated GRU.

Both models operate on the **CropNet** dataset (soybean subset) and aim to capture spatial, temporal, and multi-modal structure in a parameter-efficient way.
