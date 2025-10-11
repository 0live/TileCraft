# Initialisation:
--To change for uv
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify install: 
```python -m pip show fastapi```

# Python Linter/Formatter
Linting and formatting is managed with Ruff extension. Install extension and update settings.json as follow:
```yaml
"[python]": {
    "editor.formatOnType": true,
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": "explicit"
    }
}
```
You can also set the python type checking to standard: ```"python.analysis.typeCheckingMode": "standard"```

# Alembic
Migrations are done with Alembic
- import your SQLModel classes on env.py
```python
from app.db.users import User  # noqa
```
Then run make commands:
```bash
make create-migration
make apply-migration
```