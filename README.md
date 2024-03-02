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
    - [Running the tests locally](#running-the-tests-locally)
    - [Github setup](#github-setup)

## Infrastructure

The infrastructure is written in **aws cdk** and is found in the _/test_infrastructure_ folder.

I started out using **terraform** for infrastructure, but it was more painful than **cdk**. When I set up the testing infrastructure I used **cdk** and eventually I moved the production infrastructure to **cdk** as well as after creation you can't modify the stack name, it remained test_infrastructure.

The infrastructure is deployed with the following command:

```bash
cd test_infrastructure
cdk deploy
```

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

### Running the tests locally

The tests are run with the following command:

```bash
# you are project root
pytest . -v
# or locally
poetry run pytest . -v
```

### Github setup

For each PR a Github action workflow is run to test the code. The workflow is found in _.github/workflows_ and is called _pytest.yml_. The workflow is run on **python3.10** and **3.11** and it runs the same command as above.

For the **AWS** part the workflow has access to a real **S3 bucket** with as the credentials for the test user have been added as repository secrets and the rest is taken care of by the workflow.
