# Initialisation:
```bash
cd api/ && uv sync
```dock

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
The database is managed by Alembic
- import your SQLModel classes on /alembic/env.py
```python
from app.db.users import User  # noqa
```
Then run make commands:
```bash
make create-migration -m="Description"
make apply-migration
```