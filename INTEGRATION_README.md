# CODECRAFT 3D — Muse Spark integration foundation

This integration adds a server-side Meta Model API client, a PDF-to-candidate-constraint pipeline, and deterministic evidence traceability checks. It intentionally does **not** mark AI output as legally verified or feed it into the geometry engine automatically.

## Files

- `core/meta_client.py` — Muse Spark API request using `POST https://api.meta.ai/v1/responses`.
- `core/evidence_validator.py` — checks that the cited page exists, the excerpt occurs on that page, and the number/unit appear in the excerpt.
- `core/regulation_pipeline.py` — connects the existing PDF processor to Muse Spark and the evidence checks.
- `tests/` — unit tests that do not require an API key or paid request.

## Local setup (Git Bash)

```bash
cd "/e/CodeCraft 3D"
source ".venv/Scripts/activate"
```

Install dependencies if missing:

```bash
pip install requests python-dotenv
```

Copy `.env.example` to `.env` and add your key. The code reads `MODEL_API_KEY` from the environment. If you want `.env` auto-loading, add this once near the top of your app entry point before calling the pipeline:

```python
from dotenv import load_dotenv
load_dotenv()
```

Run tests:

```bash
python -m pytest tests/test_evidence_validator.py tests/test_meta_client.py -q
```

## Important trust boundary

The output status `extracted` means only that the excerpt and basic numeric/unit text checks passed. It does not mean `verified`. Human review is required before a regulation is treated as applicable. The current validator is deliberately conservative and may flag equivalent wording, locale-specific number formats, tables, footnotes, or units that require normalization.

The current PDF processor does not perform OCR. Image-only/scanned PDFs must be OCR-processed before extraction.
