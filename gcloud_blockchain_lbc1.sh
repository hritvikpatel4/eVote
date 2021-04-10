# This script is used to setup the blockchain stack and is run as a startup script on the blockchain clusters {level 1}

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

echo "Creating docker network"

sudo docker network create --driver bridge blockchain || true

echo "Spawning bc nodes"

for bc_num in 1 2 3
do
    sudo docker run -d \
        --name "bc$bc_num" \
        --hostname "bc$bc_num" \
        --network blockchain \
        -e CURRENT_LEVEL=1 \
        -e HIGHEST_LEVEL=2 \
        -e HIGHER_LEVEL_IP="http://34.117.6.106:80" \
        -e CLUSTER_ID=1 \
        -e CUSTOM_PORT=80 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /home/blockchain/logs:/usr/src/app/logs \
        ntwine/evote_bc:latest
done

echo "Spawning orderer nodes"

for ord_num in 1 2 3
do
    sudo docker run -d \
        --name "orderer$ord_num" \
        --hostname "orderer$ord_num" \
        --network blockchain \
        -e CURRENT_LEVEL=1 \
        -e HIGHEST_LEVEL=2 \
        -e CLUSTER_ID=1 \
        -e CUSTOM_PORT=80 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /home/blockchain/logs:/usr/src/app/logs \
        ntwine/evote_orderer:latest
done

echo "Spawning dbserver"

sudo docker run -d \
    --name db1 \
    --hostname db1 \
    --network blockchain \
    -e CURRENT_LEVEL=1 \
    -e HIGHEST_LEVEL=2 \
    -e CLUSTER_ID=1 \
    -e CUSTOM_PORT=80 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /home/blockchain/logs:/usr/src/app/logs \
    ntwine/evote_db:latest

echo "Spawning load_balancer"

sudo docker run -d \
    --name load_balancer1 \
    --hostname load_balancer1 \
    --network blockchain \
    -e CURRENT_LEVEL=1 \
    -e HIGHEST_LEVEL=2 \
    -e CLUSTER_ID=1 \
    -e CUSTOM_PORT=80 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /home/blockchain/logs:/usr/src/app/logs \
    -p 80:80 \
    ntwine/evote_lb:latest

echo "Spawning timer"

sudo docker run -d \
    --name timer1 \
    --hostname timer1 \
    --network blockchain \
    -e INTERVAL=90 \
    -e CURRENT_LEVEL=1 \
    -e HIGHEST_LEVEL=2 \
    -e CLUSTER_ID=1 \
    -e CUSTOM_PORT=80 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /home/blockchain/logs:/usr/src/app/logs \
    ntwine/evote_timer:latest

echo "Done!"
