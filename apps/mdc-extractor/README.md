# mdc-extractor

Features extractor written in Python.
Extracts musical features for machine learning from `.mscx` files.

## Getting Started

0. Make sure you're at the right place.
```shell
cd src/mdc-extractor
```
1. Ensure dependencies are installed (preferably in a virtual environment).
```shell
pip install -r requirements.txt
```

### Testing

To run tests
```shell
python -m unittest --verbose
```

### Formatting

0. Ensure `black` and `isort` is installed.
```shell
pip install black isort
```
1. Call `isort` to sort imports.
```shell
isort
```
2. Call `black` to format code.
```shell
black .
```

**Note:** for `test_extractor.py` use `black` with arguments `-l 400`
