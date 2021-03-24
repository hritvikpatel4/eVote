# This script is used to create docker images and push them to the docker registry

#! /bin/bash

echo "creating webserver image"
sudo docker build -t ntwine/evote_web:latest ./webserver
echo "creating dbserver image"
sudo docker build -t ntwine/evote_db:latest ./dbserver
echo "creating bc image"
sudo docker build -t ntwine/evote_bc:latest ./bc
echo "creating orderer image"
sudo docker build -t ntwine/evote_orderer:latest ./orderer
echo "creating load_balancer image"
sudo docker build -t ntwine/evote_lb:latest ./load_balancer

echo "pushing webserver image to docker registry"
sudo docker push ntwine/evote_web:latest
echo "pushing dbserver image to docker registry"
sudo docker push ntwine/evote_db:latest
echo "pushing bc image to docker registry"
sudo docker push ntwine/evote_bc:latest
echo "pushing orderer image to docker registry"
sudo docker push ntwine/evote_orderer:latest
echo "pushing load_balancer image to docker registry"
sudo docker push ntwine/evote_lb:latest

echo "Done!"
