# Nia — The Minister of Verdicts

Custom AI model trained on Black history, African American studies, and cultural knowledge.

## Project Structure

```
nia/
├── pdf_to_training.py      # Convert any PDF → training data (single file)
├── nia_build_dataset.py    # Batch process the full NIA LESSONS folder
├── train_nia.py            # LoRA fine-tune on RunPod / Colab
├── chat_nia.py             # Local chat interface (via Ollama)
├── generate_nia_data.py    # Persona/identity data generation
├── Modelfile               # Ollama model definition
├── training_data/
│   └── nia_build_state.json  # Resume state (tracks which PDFs are done)
└── data/                   # Persona and identity training data
```

## Build the Training Dataset

### From your PDF folder (first time)
```bash
python3 nia_build_dataset.py
```

### Resume after a Colab/RunPod timeout
```bash
python3 nia_build_dataset.py --resume
```

### Process a single PDF
```bash
python3 pdf_to_training.py myfile.pdf
python3 pdf_to_training.py myfile.pdf --chunks 0-49   # first 50 pages only
python3 pdf_to_training.py myfile.pdf --chunks 50-    # rest of the pages
python3 pdf_to_training.py myfile.pdf --merge-outputs # combine all chunks
```

Deduplication runs automatically — exact and near-duplicate passages are removed across all files and sessions.

## Train on RunPod

1. Upload this repo + `training_data/` to RunPod
2. Install deps: `pip install -r requirements.txt`
3. Run: `python3 train_nia.py`

## Train on Google Colab

Split the work across sessions using `--chunks`:
```bash
# Session 1
python3 nia_build_dataset.py --files 0-19

# Session 2 (upload nia_build_state.json first)
python3 nia_build_dataset.py --files 20-39

# Session 3
python3 nia_build_dataset.py --files 40-
```

## Chat with Nia (local)
```bash
ollama create nia -f Modelfile
python3 chat_nia.py
```
