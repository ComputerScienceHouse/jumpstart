
## Installing
1. Clone and cd into the repo: git clone https://github.com/WeatherGod3218/jumpstartV2
>> Make another branch if you are working on a large PR
2. 

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

### Alternatively, you can run the docker compose file as well
```
    docker compose up
```