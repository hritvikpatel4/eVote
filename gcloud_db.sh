# This script is used to setup the shared db instance as a startup script

#! /bin/bash

# Installs all the required software on the instance
echo "Installing software on instance"

apt update && apt upgrade -y
apt install -y python3 python3-pip
apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt update && apt install -y docker-ce docker-ce-cli containerd.io
curl -L "https://github.com/docker/compose/releases/download/1.28.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
pip3 install docker requests

rm -rf /home/blockchain
mkdir -p /home/blockchain/logs

echo "Cleaning old docker stuff"

sudo docker stop $(sudo docker ps -a -q)
sudo docker rm $(sudo docker ps -a -q)
sudo docker rmi $(sudo docker images -a -q)
echo y | sudo docker volume prune
echo y | sudo docker system prune -a
echo y | sudo docker system prune

echo "Spawning dbserver"

sudo docker run -d \
    --name db1 \
    --hostname db1 \
    -e CURRENT_LEVEL=0 \
    -e HIGHEST_LEVEL=2 \
    -e CUSTOM_PORT=80 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /home/blockchain/logs:/usr/src/app/logs \
    -p 80:80 \
    ntwine/evote_db:latest

echo "Done!"
