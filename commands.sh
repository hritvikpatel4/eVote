#!/bin/bash

# Shell script to install required softwares onto the new instance

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo curl -L "https://github.com/docker/compose/releases/download/1.28.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo pip3 install docker requests
sudo chmod +x /home/blockchain/eVote/Blockchain/create_image.sh
sudo chmod +x /home/blockchain/eVote/docker_clean.sh
sudo chmod +x /home/blockchain/eVote/docker_list.sh

# web server

# csvfile - lbc
# 1,2,3,4
# 1,0,0,0
# 1,0,0,0
# 0,0,0,1

# [[{"1":1, "2":0, "3":0, "4":0},{"1":1, "2":0, "3":0, "4":0},{"1":0, "2":0, "3":0, "4":1}],[{"1":1, "2":0, "3":0, "4":0},{"1":1, "2":0, "3":0, "4":0},{"1":0, "2":0, "3":0, "4":1}],[{"1":1, "2":0, "3":0, "4":0},{"1":1, "2":0, "3":0, "4":0},{"1":0, "2":0, "3":0, "4":1}]]

# {"1":0, "2":0, "3":0, "4":0} - 0 [genesis block]

# {"1":10, "2":5, "3":0, "4":1} - new batched lbc data

# {"1":10, "2":5, "3":0, "4":1} - 1

# {"1":140, "2":40, "3":99, "4":188} - new batched lbc data

# {"1":140, "2":45, "3":99, "4":189} - 2

# {"1":10, "2":10, "3":1, "4":11} - new batched lbc data

# {"1":150, "2":50, "3":100, "4":200} - 3

# {"1":15, "2":5, "3":10, "4":2} - new batched lbc data

# {"1":165, "2":55, "3":110, "4":202} - 4