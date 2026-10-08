---
license: apache-2.0
metrics:
- accuracy
- f1
base_model:
- google/vit-base-patch16-224-in21k
pipeline_tag: image-classification
library_name: transformers
---
**Note to users who want to use this model in production**

Beware that this model is trained on a dataset collected **about 1 year ago**. 
Since then, there is a remarkable progress in generating deepfake images with common AI tools, resulting in a significant concept drift. 
To mitigate that, I urge you to retrain the model using the latest available labeled data. 
As a quick-fix approach, simple reducing the threshold (say from default 0.5 to 0.1 or even 0.01) of labelling image as a fake may suffice. 
However, you will do that at your own risk, and retraining the model is the better way of handling the concept drift.

=======

Predicts with about 98% accuracy whether an attached image is AI-generated.

See https://www.kaggle.com/code/dima806/ai-vs-human-generated-images-prediction-vit for details.

![image/png](https://cdn-uploads.huggingface.co/production/uploads/6449300e3adf50d864095b90/vaVofgP3NO3ybwG0GSbC3.png)

```
Classification report:

              precision    recall  f1-score   support

       human     0.9655    0.9930    0.9790      3998
AI-generated     0.9928    0.9645    0.9784      3997

    accuracy                         0.9787      7995
   macro avg     0.9791    0.9787    0.9787      7995
weighted avg     0.9791    0.9787    0.9787      7995
```