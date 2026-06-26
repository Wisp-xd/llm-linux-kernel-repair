# GitHub Upload Checklist

## Recommended Repository Scope

This folder is the GitHub-ready project package. It keeps the reproducible course artifacts and removes local machine state such as virtual environments, WSL images, kernel source trees, and bulky raw kGym logs.

Keep:

- `src/`, `prompts/`, `tools/`
- `data/demo/`, `data/selected/`, `data/selected_bugs.csv`
- `outputs/` for the 8 selected cases and demo runs
- `results/` summary tables, figures, evaluation workbook, and dynamic validation summaries
- `docs/` markdown reports and selected paper assets

Do not add:

- `.venv/`, `__pycache__/`, `*.pyc`
- real `.env` files or API keys
- `presentation/` or `*.pptx` for now; keep the final defense deck as a local submission artifact
- `*.docx` or `*.pdf` final reports for now; keep Word/PDF reports as local submission artifacts
- WSL images, Linux kernel source trees, Docker volumes, or kGym build caches
- large raw VM logs unless explicitly required by the course submission

## Before Upload

```powershell
cd D:\SQA\llm-linux-kernel-repair-github
git init -b main
git add .
git status --short
```

Review the staged file list. Then commit and push:

```powershell
git commit -m "Prepare LLM kernel repair course project"
git remote add origin https://github.com/<your-user>/<your-repo>.git
git push -u origin main
```

## Quick Verification

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\src\run_all_groups.py --provider mock --limit 1 --output-root .\tmp_mock_outputs --summary-out .\tmp_mock_outputs\summary.json
```

`tmp_mock_outputs/` is only a local check artifact and should not be committed.
