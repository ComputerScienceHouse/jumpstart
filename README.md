# Jumpstart

![image](./docs/images/jumpstart_transparant.png)

![Static Badge](https://img.shields.io/badge/%40gravy-made_by?style=flat-square&logo=github&labelColor=%230d1117&color=%23E11C52&link=https%3A%2F%2Fgithub.com%2FNikolaiStrong)


A graphical interface that displays information in the elevator lobby of Computer Science House.
All information displayed has been authorized to been shown.

Documentation for the project can be found be appended /docs to the url
All HTML requests that are sent in the project can be seen by appending /swag

This project uses Python, [FastAPI](https://fastapi.tiangolo.com/), [UV](https://docs.astral.sh/uv/), HTML/CSS, and Javascript.
See it live [here](https://jumpstart.csh.rit.edu)!

## Installing
1. Clone and cd into the repo: git clone https://github.com/WeatherGod3218/jumpstartV2
>> (OPTIONAL): Make another branch if your working on a large thing!

## Setup
1. Make sure you have docker installed
>> (OPTIONAL): You can use docker compose as well!!
2. Copy the .env.template file, rename it to .env and place it in the root folder
3. Ask an RTP for jumpstart secrets, add them to the .env accordingly

## Run

Jumpstart is containerized through a docker file.

1. Build the docker file
```
    docker build -t Jumpstart .
```
2. Run the newly built docker on port 8000
```
    docker run -p 8080:80 Jumpstart
```

## Docker Compose

Jumpstart also has support for Docker Compose, a extended version of docker that simplifies the steps.

(This is a really cool thing! If you use docker often, check it out!)
```
    docker compose up
```

## Local Development

### NOTE: MAKE SURE TO USE `uv add` IN THIS PROJECT TO KEEP `pyproject.toml` and `uv.lock` UPDATED!
## UV Setup

Install UV on your system if not already on it. If you already have it installed, you can skip down to the Project Setup page

UV is a blazingly fast python package manager written in Rust. The Jumpstart project uses UV for speed and simplicity. Run the linked install command for your operating system

__Linux and macOS__
```
    curl -LsSf https://astral.sh/uv/install.sh | sh
```

__Windows (Powershell)__
```
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## UV Commands Useful For this Project

__uv sync__: UV sync serves to replace pip install -r requirements.txt. This command syncs your virtual environment to match the `pyproject.toml` file. By default, it will only copy the default dependencies for the project (found in dependencies)

__uv sync --group $GROUP__: UV sync with the added group flag will ALSO install all dependencies found in that group ALONG with the default dependencies. 

__uv sync --frozen__: When reading the UV Sync, it reads ONLY the `uv.lock` file, and does not attempt to make any modifications, and failing instead. This is incredibly useful for reproducibility, which is why its used in the docker file.

__uv sync --all-groups__: UV sync, along with installing dependencies of every group

__uv add $PACKAGE__: UV serves to replace pip install $PACKAGE. It installs the most recent version of the inserted package, and adds it to the projects default dependencies

__uv add --group $GROUP $PACKAGE__: Same as UV add, but adds the package to the group instead of the default project dependencies. 

## UV Groups Used in this Project
__dev__: Dependencys needed for testing locally

__docs__: Dependencys used for creating the statically generated website on /docs

__tests__: Dependencys used for running the unit tests.

## Project Setup
1. Run: `uv venv .venv` --python 3.14
2. Activate the virtual environment
    * Bash: `source .venv/bin/activate`
    * Fish: `source .venv/bin/activate.fish`
    * Windows: `.venv\Scripts\activate`
    * Other: Good luck!
3. Run: `uv sync --all-groups`
4. Run: `pre-commit install`
5. You're all set!

### Testing

We're using the pytest framework to create tests. A good minimum coverage requirement is about <=90%.

To run the tests just run: `pytest`

`coverage.xml` and `htmlcov` should be generated. `coverage.xml` is used for Sonarqube, while `htmlcov` is a local html view into code coverage. The easiest way to view the coverage site is to enter the directory and run: `python -m http.server` and visit the site!
