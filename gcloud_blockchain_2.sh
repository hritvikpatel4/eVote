# This script is used to setup the blockchain stack and is run as a startup script on the blockchain clusters

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

docker stop $(sudo docker ps -a -q)
docker rm $(sudo docker ps -a -q)
docker rmi $(sudo docker images -a -q)
echo y | docker volume prune
echo y | docker system prune -a
echo y | docker system prune

echo "Creating docker network"

docker network create --driver bridge blockchain || true

echo "Spawning bc nodes"

for bc_num in 1, 2, 3, 4
do
    docker run -d \
        --name bc$bc_num \
        --hostname bc$bc_num \
        --network blockchain \
        -e CURRENT_LEVEL=2 \
        -e HIGHEST_LEVEL=2 \
        -e CUSTOME_PORT=80 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /home/blockchain/logs:/usr/src/app/logs \
        ntwine/evote_bc:latest

echo "Spawning orderer nodes"

for ord_num in 1, 2, 3
do
    docker run -d \
        --name orderer$ord_num \
        --hostname orderer$ord_num \
        --network blockchain \
        -e CURRENT_LEVEL=2 \
        -e HIGHEST_LEVEL=2 \
        -e CUSTOME_PORT=80 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /home/blockchain/logs:/usr/src/app/logs \
        ntwine/evote_orderer:latest

echo "Spawning load_balancer"

docker run -d \
    --name load_balancer1 \
    --hostname load_balancer1 \
    --network blockchain \
    -e CURRENT_LEVEL=2 \
    -e HIGHEST_LEVEL=2 \
    -e CUSTOME_PORT=80 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /home/blockchain/logs:/usr/src/app/logs \
    -p 80:80 \
    ntwine/evote_lb:latest

echo "Spawning databaseserver"

docker run -d \
    --name db1 \
    --hostname db1 \
    -e CURRENT_LEVEL=2 \
    -e HIGHEST_LEVEL=2 \
    -e CUSTOME_PORT=80 \
    -e DB_IP=""
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /home/blockchain/logs:/usr/src/app/logs \
    -p 80:80 \
    ntwine/evote_db:latest
