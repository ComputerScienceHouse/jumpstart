# Jumpstart
## Author: Beckett Jenen

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

A graphical interface that runs on a RPI in the lobby of my dorm.

## Install

This project uses [Python](http://nodejs.org), [Flask](https://npmjs.com), SQL, HTML/CSS, and Javascript. 

1. Download the zip file and open the code.
2. Navigate into the project's folder.
3. Run `pip install -r requirements.txt`
6. Ask opcomm for secrets
    - The secrets package follows the directory structure:
    src/
      secrets/
        client_secrets.json
5. Run `flask --app jumpstart run`
6. Results

Jumpstart expects the following environment variables to be defined:
```
FLASK_APP=jumpstart:App
JUMPSTART_API_KEYS=KEYS
TZ=TIMEZONE
SENTRY_DSN=LINK
```
## Docker

1. Ensure you are in the project root, then build the image locally with `docker built -t jumpstart .`
2. Run with the following: (Be sure to update env variables)
```
docker run \
    -e FLASK_RUN_HOST=0.0.0.0 \
    -e FLASK_APP=jumpstart:App \
    -e JUMPSTART_API_KEYS=KEYS \
    -e TZ=America/New_York \
    -e SENTRY_DSN=LINK \
    -v ./secrets:/usr/local/jumpstart/secrets \
    -p 5000:5000 \
    jumpstart
```


## Usage

Go [here](https://jumpstart.csh.rit.edu)
