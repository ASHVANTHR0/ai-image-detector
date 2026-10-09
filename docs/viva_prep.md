# Viva preparation

Short, defensible answers grounded in this project. Numbers come from `docs/final_report.md` and the result files it
cites.

---

**1. What does your system do, in one sentence?**
It takes an uploaded image and returns the probability that it is AI-generated plus a decision (AI / real /
uncertain) with a confidence level. It runs fully offline with open-source models.

**2. What accuracy did you get?**
On our sealed test set of 466 OpenFake images it scored 91.4% accuracy (95% CI 88.6–94.0%) and ROC-AUC 0.975. It
abstains on 11.6% of images; on the rest it is 95.4% accurate with 4.2% false positives. On 199 images from generators
it never saw, it scored 93.5%. I don't claim it works this well on every image on the internet.

**3. Why not claim 100%?**
Generators keep changing, images get compressed and edited, and any detector has false positives and false
negatives. A 100% claim on arbitrary images can't be verified. I report measured numbers on defined data, with
confidence intervals.

**4. Why transfer learning instead of training from scratch?**
We have about 3,000 images and a 6 GB laptop GPU. A network trained from scratch would overfit badly. CLIP ViT-B/16
was pretrained on 400 million image-text pairs, so its features already capture image statistics, and only the head
(or a small fine-tune) needs our data. Our full fine-tune still overfit (99.9% train vs 85.9% validation accuracy),
which shows how little data we have.

**5. Why a frozen-CLIP linear probe and a fully fine-tuned CLIP?**
They fail differently. Following Ojha et al. (CVPR 2023), the frozen backbone can't memorize the training generators'
artifacts, so it generalizes: it was the best single member on unseen generators (AUC 0.958). The fine-tuned model is
best in-distribution (test AUC 0.967) but weaker on unseen generators (0.931). The ensemble takes the strengths of both.

**6. How did you prevent data leakage?**
- Exact duplicates removed by SHA-256.
- Near-duplicates (perceptual hash, Hamming distance ≤ 6) share a group, and whole groups go to one split.
- Images that appear in the benchmark were excluded from training.
- `dataset_tool.py check` verifies that no hash or group spans two splits, and it passed.
- The scripts refuse to read the test split except from the final evaluation.

**7. How did you avoid "format shortcuts"?**
Every image of both classes is re-encoded the same way (RGB, max 1024 px, JPEG q95), so "PNG = AI" can't be learned.
Training also applies random JPEG compression to both classes. One remaining confound I report is resolution: AI
images have a median of 1024 px, real ones 683 px.

**8. Why does the UNCERTAIN class exist? Is it a training class?**
It's not a training class; it's a decision outcome. If the ensemble probability falls between `t_low = 0.23` and
`t_high = 0.74`, the system says "uncertain" instead of guessing. This is selective classification. It cut the false
positive rate from 7.1% to 4.2% on test, and from 4.1% to 1.7% on unseen generators.

**9. How were the thresholds chosen?**
On the validation split only. `fit_ensemble.py` searches for the widest coverage that keeps decided accuracy ≥ 95%
and FPR, FNR < 5%. On validation that gave 84% coverage; on test we got 88%, so the thresholds weren't overfit.

**10. Why was the test set evaluated only once?**
If you look at the test set and then change anything, the test set becomes another validation set and the reported
number is optimistic. We froze the model, thresholds and weights first, recorded their hashes and the git commit in
`FREEZE.md`, then ran it once. The script refuses to run twice without a logged reason.

**11. How does the ensemble combine models?**
Logistic stacking over log-odds: p = σ(b + Σ wᵢ · logit(sᵢ)). Members have different calibration (one pretrained
model is very overconfident), and stacking learns how much to trust each. We also tried a weighted average and
majority vote. Stacking had the best log loss on validation. A member with a negative weight (siglip) was removed.

**12. Did the ensemble actually help? (RQ2)**
Yes. On test, the best single model reached 89.1% accuracy (FPR 10.8%) and the ensemble 91.4% (FPR 7.1%). On unseen
generators: 90.0% vs 93.5%.

**13. What did error analysis change?**
An earlier ensemble looked excellent on the benchmark (95%) but flagged 21.5% of *our* real photos as AI, because its
weights were fitted on differently processed images. We added the fine-tuned CLIP model and refitted on our own
validation split, which roughly halved real-photo false positives before the test was ever opened.

**14. Why does accuracy drop under JPEG compression? (RQ4)**
Generators leave subtle high-frequency traces. Strong JPEG compression removes high frequencies, so AI images start
to look like ordinary compressed photos. At quality 30, the share of AI images we miss rises from 9.7% to 44.7%.
Downscaling and screenshot-style PNG barely matter, since the models resize to 224 px anyway.

**15. Why don't you trust metadata?**
Metadata is trivial to strip or forge. We use it in one direction only: a valid signed C2PA manifest or embedded
generation parameters can *confirm* AI origin. Missing metadata proves nothing, so it never pushes a decision
towards "real".

**16. Why not just use AI or Not (or another paid API)?**
Cost, usage limits, network dependence, a closed model we can't inspect, and results we can't reproduce. The
project's objective is a free, local, reproducible system.

**17. How does it run offline at ₹0?**
Everything is open source (PyTorch, Transformers, timm, FastAPI, SQLite, Vue). After `download_models.py` fetches
the weights once, no network access is needed. Inference takes about 52 ms per image on an RTX 4050, and it also runs
on CPU, more slowly.

**18. Which generators fool it?**
On test: FLUX.1-dev (60% caught) and FLUX 1.1 Pro (62.5%). On unseen generators: Midjourney 7 (5 of 7) and
images scraped from Reddit (4 of 7). Sample sizes per generator are small, so these are indications, not
conclusions.

**19. Is your cross-generator test truly independent?**
The benchmark holdout uses OpenFake *test* generators that aren't in our training data, and v3b was never tuned on
it. Two caveats: an earlier ensemble (v1) had been scored on it once, and it's a differently processed distribution
from our own test set. We didn't build a separate `test_unseen` split inside our own dataset.

**20. What would you do with more time?**
- More data from more generators and real-photo sources, with matched resolutions.
- Stronger compression augmentation, since compression is our biggest weakness.
- Frequency-domain members.
- Heatmap explanations.
- Periodic retraining as new generators appear.

**21. How can someone reproduce your results?**
Every run has a config, seed 42 and a dataset version hash. Results come from saved `predictions.csv` files through
one metrics module, `evaluation/metrics.py`. The README lists the commands for each phase.

**22. What are the main limitations?**
- No universal guarantee.
- Weak against heavy compression.
- Resolution confound in the data.
- Small single-source training set.
- 7% false positives when forced to decide.
- Per-generator samples are small.
