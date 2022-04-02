# mdc-django

Server for the MDC application, written in Python with Django.

## Getting Started

0. Make sure you're at the right place.
```shell
cd src/mdc-django
```
1. Ensure dependencies are installed (preferably in a virtual environment).
```shell
pip install -r requirements.txt
```
2. Run the development server.
```shell
python manage.py runserver
```

3. Ensure client JS bundle is compiled in `mdc-ui` (see [`mdc-ui`](../mdc-ui)).

### Testing

To run tests
```shell
python manage.py test
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
