# Audiobook Project

This repository contains a simple audiobook generation workflow using OpenAI-compatible TTS and story generation helpers.

## Repository structure

- `notebooks/`
  - `audiobook_demo.ipynb` — demo of audio generation for a sample synopsis and full story.
  - `audiobook_workflow.ipynb` — workflow notebook for text review, preview audio, and full audio generation.
- `output/`
  - stores generated sample and full story audio files.
- `sample_voices/`
  - stores generated voice sample MP3 files.
- `audiobook_prd.md`
  - product requirements and personalization reference used by the story generation helper.
- `whisper_client.py`
  - helper functions for story generation and text-to-speech conversion.
- `.gitignore`
  - ignores environment, `venv/`, and `__pycache__/`.

## Setup

1. Create and activate a Python virtual environment:

I am using python 3.12 at the development machine. Feel free to choose whatever version, cannot guarantee if it will work if it's not 3.12.

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your OpenAI key:

```bash
cp .env.example .env
# or manually create .env with OPENAI_API_KEY
```

4. Add your `OPENAI_API_KEY` to `.env`:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

## Usage

Open one of the notebooks in `notebooks/` and run the cells step by step.

### `notebooks/audiobook_workflow.ipynb`

1. Load libraries, configuration, and paths.
2. Generate story text only from the prompt and PRD.
3. Review the generated text.
4. Generate a short preview audio from the approved story text.
5. Generate the full audiobook audio from the same story text.

### `notebooks/audiobook_demo.ipynb`

1. Generate a sample synopsis audio file.
2. Generate a full-story audio file.
3. Play the generated audio inline.

## Folder notes

- Put generated story audio into `output/`.
- Put generated voice samples into `sample_voices/`.
- Keep notebooks inside `notebooks/`.

## Important

Do not commit your local `venv/` or `__pycache__/` folders. The `.gitignore` is already configured to ignore them.
