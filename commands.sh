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
git clone https://github.com/hritvikpatel4/eVote.git
sudo chmod +x eVote/Blockchain/create_image.sh
sudo chmod +x eVote/docker_clean.sh
sudo chmod +x eVote/docker_list.sh