<script setup>
const steps = [
  ['Upload', 'The image is checked: size limit, real file format (not just the extension), and that it decodes.'],
  ['Preprocess', 'Orientation is fixed and the image is converted to RGB, exactly as during training.'],
  ['Detectors', 'Several open-source deep-learning detectors each estimate the probability that the image is AI generated.'],
  ['Ensemble', 'Their scores are combined with weights tuned on a validation set.'],
  ['Decision', 'High scores mean AI generated, low scores mean real; anything in between is reported as Uncertain.'],
  ['Store', 'The result and a hash of the file are saved in a local SQLite database. The image itself is not kept.'],
]
const limitations = [
  'AI-image detection is not universally reliable, and 100% real-world accuracy cannot be guaranteed.',
  'New image generators may not be recognised by detectors trained on older ones.',
  'Editing, resizing, screenshots and heavy JPEG compression can reduce accuracy.',
  'Training data can contain biases and generator-specific artifacts.',
  'Metadata (EXIF) can be removed or changed, so it is shown for information only.',
]
</script>

<template>
  <div class="max-w-3xl space-y-8">
    <section>
      <h1 class="text-2xl font-semibold text-slate-900">About this project</h1>
      <p class="mt-3 text-slate-700">
        A completely free, locally deployable AI-generated image detection system using open-source deep-learning models.
        It classifies images as <b>AI generated</b>, <b>real</b> or <b>uncertain</b>, and its performance is evaluated across
        diverse datasets and multiple image generators, including generators never seen in training.
      </p>
      <p class="mt-2 text-slate-700">No paid API and no cloud service: after the models are downloaded, everything runs on this computer.</p>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold">How it works</h2>
      <ol class="space-y-3">
        <li v-for="([title, text], i) in steps" :key="title" class="card flex gap-4 !p-4">
          <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white">{{ i + 1 }}</span>
          <div><p class="font-medium">{{ title }}</p><p class="text-sm text-slate-600">{{ text }}</p></div>
        </li>
      </ol>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold">Technology</h2>
      <p class="text-sm text-slate-700">Python · PyTorch · Hugging Face Transformers · timm · FastAPI · SQLite · Vue.js · Tailwind CSS · Chart.js</p>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold">Limitations</h2>
      <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
        <li v-for="l in limitations" :key="l">{{ l }}</li>
      </ul>
      <p class="mt-3 text-sm text-slate-600">Treat results as evidence to weigh, not as proof.</p>
    </section>
  </div>
</template>
