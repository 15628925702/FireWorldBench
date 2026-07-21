# Model Input Adapters

The fixed evaluation model is openai/gpt-4o-mini. Its declared input modalities
are text, image, and file; it does not declare video input.

- S uses structured JSON from the public observation and, for L1-2, public
  candidate assets. Asset references are resolved under the declared public root.
- I uses each frozen observation PNG and each L1-2 candidate image as an
  OpenAI-compatible image data URL. Image paths alone are never treated as input.
- V is unsupported for this fixed model. No video-to-frame conversion is used to
  label an I-style proxy as a V result. A future V run requires a model with a
  declared video input modality and a versioned V adapter/preflight.

All adapters remain read-only over the immutable public release. The run manifest
records the selected input adapter and public asset root.