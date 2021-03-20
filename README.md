# Tastemade Scraper

This repository was built in order to use real recipes in the Recipeful Project of the IoT subject at University Federal of Ceará. It was used the Selenium WebDriver in Python.

## Libraries and tools used

- [Python 3.x](https://www.python.org/)
- [Selenium](https://selenium-python.readthedocs.io/)

## How to run

### Install dependencies

You can install the dependencies in two ways:

1.  ```
    pipenv install
    ```

2.  ```
    pip3 install -r requirements.txt
    ```

### Run

You need to specify the output path in the `scraper.py` script.

```
python3 scraper.py
```

## Output Format

```json
[
    {
        "url": "path to recipe",
        "name": "recipe's name",
        "category": "category's name",
        "image_url": "path to recipe image",
        "preparation_time": "time to prepare the recipe",
        "cooking_time": "time to cook",
        "portions": "how many people can be server",
        "ingredients": ["list of ingredients"],
        "intructions": ["list of intructions"]
    }
]
```

## TODO

- [ ] Pass output path as args.