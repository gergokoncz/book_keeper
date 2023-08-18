# BookKeeper

A streamlit application to keep track of the books that you are reading or plan on reading. The app is deployed on [Streamlit Share](https://bookkeeper.streamlit.app/).

## Installation

## Deployments

For local development and dependency management I run a poetry project but I do not commit it to the repo as Streamlit Share does not work well with the poetry installation. It also gets confused when there is poetry and requirements.txt files in the same repo, so the poetry part is ignored for the deployment.

When dependencies are updated I run the following command to update the requirements.txt file:

```bash
poetry export --without-hashes --format=requirements.txt > requirements.txt
```

But for local deployment the command to run is

```bash
poetry run streamlit run src/1_📈_Overview.py
```

Of course you can always use the requirements.txt file to install the dependencies and run the app with the following commands:

```bash
streamlit run src/1_📈_Overview.py
```
