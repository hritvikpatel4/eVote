# This script is used to stop all the instances in google cloud

#! /bin/bash

echo "Stopping all instances"
# gcloud compute instances stop webserver-1 \
#     --zone=us-central1-a

# gcloud compute instances stop webserver-2 \
#     --zone=us-central1-a

# gcloud compute instances stop dbserver \
#     --zone=us-central1-a

gcloud compute instances stop lbc-cluster-1 \
    --zone=us-central1-a

# gcloud compute instances stop lbc-cluster-2 \
#     --zone=us-central1-a

# gcloud compute instances stop hbc-cluster-1 \
#     --zone=us-central1-a
