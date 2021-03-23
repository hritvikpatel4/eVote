# This script is used to start all the instances in google cloud

#! /bin/bash

echo "Starting all instances"
gcloud compute instances start dbserver \
    --zone=us-central1-a

# gcloud compute instances start hbc-cluster-1 \
#     --zone=us-central1-a

# gcloud compute instances start lbc-cluster-1 \
#     --zone=us-central1-a

# gcloud compute instances start lbc-cluster-2 \
#     --zone=us-central1-a

gcloud compute instances start webserver-1 \
    --zone=us-east1-b

gcloud compute instances start webserver-2 \
    --zone=us-east1-b

echo "Done!"
