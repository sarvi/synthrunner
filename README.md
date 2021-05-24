# synthrunner
A Locust runner to run locust tests as synthetic tests to monitor services in production


## Development Steps
Install pipenv package 
```
pip3 install pipenv
```

Install a virtualenv for development
```
cd synthrunner/
pipenv install --dev
```

Install the package into the virtualenv for development and testing
```
pipenv install -e .
```

Options to run the synthrunner
```
pipenv run synthrunner
```
OR
```
pipenv shell
synthrunner
```

Run the synthrunner tests
```
pipenv run pytest
```

Linting the synthrunner code
```
pipenv run flake8 synthrunner
```

Static type checking
```
pipenv run python -m mypy synthrunner/*.py
```


Generate Documentationn

```
pipenv run sphinx-quickstart
pipenv run sphinx-build -b html docs/source docs/build_html
```