---
license: apache-2.0
language:
- en
base_model:
- google/siglip2-base-patch16-224
pipeline_tag: image-classification
library_name: transformers
---
#  **AI-vs-Deepfake-vs-Real-Siglip2**  

**AI-vs-Deepfake-vs-Real-Siglip2** is an image classification vision-language encoder model fine-tuned from google/siglip2-base-patch16-224 for a single-label classification task. It is designed to distinguish AI-generated images, deepfake images, and real images using the SiglipForImageClassification architecture.  

The model categorizes images into three classes:  
- **Class 0:** "AI" – The image is fully AI-generated, created by machine learning models.  
- **Class 1:** "Deepfake" – The image is a manipulated deepfake, where real content has been altered.  
- **Class 2:** "Real" – The image is an authentic, unaltered photograph.  

# **Run with Transformers🤗**

```python
!pip install -q transformers torch pillow gradio
```

```python
import gradio as gr
from transformers import AutoImageProcessor
from transformers import SiglipForImageClassification
from transformers.image_utils import load_image
from PIL import Image
import torch

# Load model and processor
model_name = "prithivMLmods/AI-vs-Deepfake-vs-Real-Siglip2"
model = SiglipForImageClassification.from_pretrained(model_name)
processor = AutoImageProcessor.from_pretrained(model_name)

def image_classification(image):
    """Classifies an image as AI-generated, deepfake, or real."""
    image = Image.fromarray(image).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()
    
    labels = model.config.id2label
    predictions = {labels[i]: round(probs[i], 3) for i in range(len(probs))}
    
    return predictions

# Create Gradio interface
iface = gr.Interface(
    fn=image_classification,
    inputs=gr.Image(type="numpy"),
    outputs=gr.Label(label="Classification Result"),
    title="AI vs Deepfake vs Real Image Classification",
    description="Upload an image to determine whether it is AI-generated, a deepfake, or a real image."
)

# Launch the app
if __name__ == "__main__":
    iface.launch()
```
    Classification report:
    
                  precision    recall  f1-score   support
    
              AI     0.9794    0.9955    0.9874      1334
        Deepfake     0.9931    0.9782    0.9856      1333
            Real     0.9992    0.9977    0.9985      1333
    
        accuracy                         0.9905      4000
       macro avg     0.9906    0.9905    0.9905      4000
    weighted avg     0.9906    0.9905    0.9905      4000

# **Intended Use:**  

The **AI-vs-Deepfake-vs-Real-Siglip2** model is designed to classify images into three categories: **AI-generated, deepfake, or real**. It helps in identifying whether an image is fully synthetic, altered through deepfake techniques, or an unaltered real image.  

### Potential Use Cases:  
- **Deepfake Detection:** Identifying manipulated deepfake content in media.  
- **AI-Generated Image Identification:** Distinguishing AI-generated images from real or deepfake images.  
- **Content Verification:** Supporting fact-checking and digital forensics in assessing image authenticity.  
- **Social Media and News Filtering:** Helping platforms flag AI-generated or deepfake content.  