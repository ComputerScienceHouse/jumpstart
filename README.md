# Jumpstart

![image](./docs/images/jumpstart_transparant.png)

![Static Badge](https://img.shields.io/badge/%40gravy-made_by?style=flat-square&logo=github&labelColor=%230d1117&color=%23E11C52&link=https%3A%2F%2Fgithub.com%2FNikolaiStrong)


A graphical interface that displays information in the elevator lobby of Computer Science House.
All information displayed has been authorized to been shown.

This project uses Python, [FastAPI](https://fastapi.tiangolo.com/), HTML/CSS, and Javascript. 
See it live [here](http://jumpstart-squared.cs.house/)!

## Installing
2. Clone and cd into the repo: `git clone https://github.com/WeatherGod3218/jumpstartV2
>> (OPTIONAL): Make another branch if your working on a large thing!

## Setup
1. Make sure you have docker installed
>> (OPTIONAL): You can use docker compose as well!!
2. Copy the .env.template file, rename it to .env and place it in the root folder
3. Ask an RTP for jumpstart secrets, add them to the .env accordingly

## Run 
1. Build the docker file
```
    docker build -t Jumpstart .
```
2. Run the newly built docker on port 8000
```
    docker run -p 8080:80 Jumpstart
```

## Alternatively, you can run the docker compose file as well
```
    docker compose up
```

