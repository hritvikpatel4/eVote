#!/bin/bash

# Shell script to list docker containers, images, volumes

sudo docker ps -a
printf "\n"
sudo docker images -a
printf "\n"
sudo docker volume ls