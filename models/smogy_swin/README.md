---
license: cc-by-nc-4.0
base_model:
- Organika/sdxl-detector
library_name: transformers
tags:
- image-classification
---
# AI-image-detector
The purpose of this model is to classify images as AI generated or Real.
### Dataset
This model was created by fine-tuning the [Organika/sdxl-detector] on dataset of AI generated and real images from reddit, kaggle and real art from public domain with their text description. 
Dataset was balanced to have similar number of real and generated images in each class (e.g. art, photos ...). 
Art images from public domain were paired with generated equivalent created from their text descriptions with style transfer (sdxl with ip-adapter) from original piece. 
The final dataset consisted of more than 50k images.
### Testing
The testing dataset consisted of 20% split of our base dataset and images outside the training domain from specific popular (as of 2024) image generation models.
Finetuning vastly improved performance over Organika/sdxl-detector during testing, especially on images created by newer models. 


Test split evaluation
| Accuracy |  Precision | Recall | F1 |
|:-------------:|:---------------:|:--------:|:--------:|
| 0.9818    | 0.9829        | 0.9810   | 0.9819 |

Out of domain evaluation
| Generative Model Family |  Accuracy |
|:-------------:|:---------------:|
| DALL-E          | 0.9076        |
| FluxAi          | 0.8333        |
| Imagen          | 0.7563        |
| StableDiffusion | 0.8754        |


### License
The data used to fine-tune this model was scraped from image dedicated subreddits, some of which may be copyrighted. For this reason, this model should be considered appropriate only for non-commercial use only.