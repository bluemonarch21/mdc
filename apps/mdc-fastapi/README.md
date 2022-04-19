# mdc-fastapi

1. Install requirements (in a virtual environment)
```shell
pip install -r requirements.txt
```

**Note:** `pycaret` supports Python 3.9 only on Ubuntu.
Windows should use Python 3.8

2. Run dev server with hot reload
```shell
uvicorn app.main:app --reload
```

API docs at : 
http://127.0.0.1:8000/docs
