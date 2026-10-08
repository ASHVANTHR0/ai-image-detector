---

inference: false

license: apache-2.0

tags:
- generated_from_trainer
datasets:
- imagefolder
metrics:
- accuracy
model-index:
- name: AI-generated_images_detector
  results:
  - task:
      name: Image Classification
      type: image-classification
    dataset:
      name: imagefolder
      type: imagefolder
      config: default
      split: validation
      args: default
    metrics:
    - name: Accuracy
      type: accuracy
      value: 0.9735697557711609
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# AI-generated_images_detector

This model achieves the following results on the evaluation set:
- Loss: 0.0987
- Accuracy: 0.9736

# To utilize this model

``` python

from PIL import Image
from transformers import pipeline
classifier = pipeline("image-classification", model="NYUAD-ComNets/NYUAD_AI-generated_images_detector")
image=Image.open("path_to_image")
pred=classifier(image)
print(pred)

```

## Training and evaluation data





### Training results

| Training Loss | Epoch | Step | Validation Loss | Accuracy |
|:-------------:|:-----:|:----:|:---------------:|:--------:|
| 0.0431        | 0.55  | 100  | 0.1672          | 0.9568   |
| 0.0139        | 1.1   | 200  | 0.2338          | 0.9398   |
| 0.0201        | 1.66  | 300  | 0.1291          | 0.9655   |
| 0.0023        | 2.21  | 400  | 0.1147          | 0.9709   |
| 0.0033        | 2.76  | 500  | 0.0987          | 0.9736   |


# BibTeX entry and citation info

```
@article{aldahoul2024detecting,
  title={Detecting AI-Generated Images Using Vision Transformers: A Robust Approach for Safeguarding Visual Media Integrity},
  author={AlDahoul, Nouar and Zaki, Yasir},
  journal={Available at SSRN},
  year={2024}
}

@misc{ComNets,
      url={https://huggingface.co/NYUAD-ComNets/NYUAD_AI-generated_images_detector](https://huggingface.co/NYUAD-ComNets/NYUAD_AI-generated_images_detector)},
      title={NYUAD_AI-generated_images_detector},
      author={Nouar AlDahoul, Yasir Zaki}
}

