# Jumpstart V2: Electric Boogaloo

![image](./docs/images/jumpstart_transparant.png)

![Static Badge](https://img.shields.io/badge/%40gravy-made_by?style=flat-square&logo=github&labelColor=%230d1117&color=%23E11C52&link=https%3A%2F%2Fgithub.com%2FNikolaiStrong)


A graphical interface that displays important information at the entrance of CSH.
This is a backend re-write of the previous jumpstart.

See it live [here](https://jumpstart.csh.rit.edu)!

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

