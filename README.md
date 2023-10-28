# BookKeeper

A streamlit application to keep track of the books that you are reading or plan on reading. The app is deployed on [Streamlit Share](https://bookkeeper.streamlit.app/).

## Table of Contents

- [BookKeeper](#bookkeeper)
  - [Table of Contents](#table-of-contents)
  - [Infrastructure](#infrastructure)
  - [Installation](#installation)
  - [Deployments](#deployments)
  - [Authentication](#authentication)
  - [Testing](#testing)
    - [Running the tests](#running-the-tests)

## Infrastructure

...

## Installation

For local development the project uses [poetry](https://python-poetry.org/) for dependency management. To install the dependencies run the following command:

```bash
poetry install
```

But the poetry files are not committed to the repo as Streamlit Share does not work well with the poetry installation, so the dependencies are also listed in the _requirements.txt_ file. To install the dependencies from the requirements.txt file run the following command:

```bash
pip install -r requirements.txt
```

To see how the _requirements.txt_ is generated from poetry go to the[Deployments](#deployments) section.

## Deployments

For local development and dependency management I run a **poetry** project but I do not commit it to the repo as Streamlit Share does not work well with the poetry installation. It also gets confused when there is poetry and _requirements.txt_ files in the same repo, so the **poetry** part is ignored for the deployment.

When dependencies are updated I run the following command to update the _requirements.txt_ file:

```bash
poetry export --without-hashes --format=requirements.txt > requirements.txt
```

But for local deployment the command to run is

```bash
poetry run streamlit run src/1_📈_Overview.py
```

Of course you can always use the _requirements.txt_ file to install the dependencies and run the app with the following commands:

```bash
streamlit run src/1_📈_Overview.py
```

## Authentication

The following post was followed: [blog](https://blog.streamlit.io/streamlit-authenticator-part-1-adding-an-authentication-component-to-your-app/)

## Testing

For testing **pytest** is used and the tests are found in _/src/tests_. At the moment proper test coverage is a work in progress.
As far as infrastructure goes a separate bucket has been set up with a separate user who has rights for the testing bucket but not the production one. Obviously, that would have been pretty bad practice. For more on infrastructure see the [Infrastructure](#infrastructure) section.

### Running the tests

The tests are run with the following command:

```bash
# you are project root
pytest . -v
# or locally
poetry run pytest . -v
```
