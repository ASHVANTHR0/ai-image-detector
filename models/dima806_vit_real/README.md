---
license: apache-2.0
metrics:
- accuracy
- f1
base_model:
- google/vit-base-patch16-224-in21k
---
Checks whether the image is real or fake (AI-generated).

**Note to users who want to use this model in production:**

Beware that this model is trained on a dataset collected about 2 years ago. Since then, there is a remarkable progress in generating deepfake images with common AI tools, resulting in a significant concept drift. To mitigate that, I urge you to retrain the model using the latest available labeled data. As a quick-fix approach, simple reducing the threshold (say from default 0.5 to 0.1 or even 0.01) of labelling image as a fake may suffice. However, you will do that at your own risk, and retraining the model is the better way of handling the concept drift.

See https://www.kaggle.com/code/dima806/cifake-ai-generated-image-detection-vit for more details.

![image/png](https://cdn-uploads.huggingface.co/production/uploads/6449300e3adf50d864095b90/bbtmz7duMA6o4HfEp_vjz.png)

```
Classification report:

              precision    recall  f1-score   support

        REAL     0.9868    0.9780    0.9824     24000
        FAKE     0.9782    0.9870    0.9826     24000

    accuracy                         0.9825     48000
   macro avg     0.9825    0.9825    0.9825     48000
weighted avg     0.9825    0.9825    0.9825     48000
```