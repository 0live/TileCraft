# Initialisation:
python -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip

pip install -r requirements.txt

Verify install: python -m pip show fastapi

# Python Linter/Formatter
Linting and formatting is managed with Ruff extension. Update settings.json as follow:
```
"[python]": {
    "editor.formatOnType": true,
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": "explicit"
    }
}
```
# Alembic
Migrations are done with Alembic
- make init-alembic
- edit sqlalchemy.url in alembic.ini