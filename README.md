# Jumpstart

![image](./docs/images/jumpstart_transparant.png)

![Static Badge](https://img.shields.io/badge/%40gravy-made_by?style=flat-square&logo=github&labelColor=%230d1117&color=%23E11C52&link=https%3A%2F%2Fgithub.com%2FNikolaiStrong)


A graphical interface that displays information in the elevator lobby of Computer Science House.
All information displayed has been authorized to been shown.

Documentation for the project can be found be appended /docs to the url
All HTML requests that are sent in the project can be seen by appending /swag

This project uses Python, [FastAPI](https://fastapi.tiangolo.com/), HTML/CSS, and Javascript.
See it live [here](http://jumpstart-cubed.cs.house/)!

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

## Development

### Setup
1. Install uv on your system if not already on it (this just makes it easy)
2. Run: `uv venv .venv`
3. Activate the virtual environment
    * Bash: `source .venv/bin/activate`
    * Fish: `source .venv/bin/activate.fish`
    * Windows: `.venv\Scripts\activate`
    * Other: Good luck!
4. Run:
    * `uv pip install -r dev-requirements.txt`
    * `uv pip install -r src/requirements.txt`
    * `uv pip install -r tests/requirements,txt`
    * `uv pip install -r docs/requirements.txt`
5. Run: `pre-commit install`
6. You're all set!

### Testing

We're using the pytest framework to create tests. A good minimum coverage requirement is about <=90%.

To run the tests just run: `pytest`

`coverage.xml` and `htmlcov` should be generated. `coverage.xml` is used for Sonarqube, while `htmlcov` is a local html view into code coverage. The easiest way to view the coverage site is to enter the directory and run: `python -m http.server` and visit the site!
