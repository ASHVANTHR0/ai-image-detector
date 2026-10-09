# Experiments

| Experiment ID | Dataset version | Model version | Parameters | Seed | Date | Validation score | Test score |
|---|---|---|---|---|---|---|---|
| 20261009-230954-clip_linear | e59e60ea7dea7fb1 | vit_base_patch16_clip_224.openai | lr=2e-05, bs=32x1, epochs<=0, wd=0.0 | 42 | 20261009 | acc 0.7863, F1 0.7807, AUC 0.8525 | — |
| 20261009-231902-clip_vitb16 | e59e60ea7dea7fb1 | vit_base_patch16_clip_224.openai | lr=2e-05, bs=16x2, epochs<=8, wd=0.05 | 42 | 20261009 | acc 0.8590, F1 0.8571, AUC 0.9395 | — |
