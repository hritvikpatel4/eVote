# This script is used to update the startup script on all the instances in google cloud

#! /bin/bash

echo "Adding startup script metadata to all instances"
gcloud compute instances add-metadata webserver-1 \
    --metadata-from-file startup-script=./gcloud_web.sh \
    --zone=us-east1-b

gcloud compute instances add-metadata webserver-2 \
    --metadata-from-file startup-script=./gcloud_web.sh \
    --zone=us-east1-b

gcloud compute instances add-metadata dbserver \
    --metadata-from-file startup-script=./gcloud_db.sh \
    --zone=us-central1-a

gcloud compute instances add-metadata lbc-cluster-1 \
    --metadata-from-file startup-script=./gcloud_blockchain_lbc1.sh \
    --zone=us-central1-a

gcloud compute instances add-metadata lbc-cluster-2 \
    --metadata-from-file startup-script=./gcloud_blockchain_lbc2.sh \
    --zone=us-central1-a

gcloud compute instances add-metadata hbc-cluster-1 \
    --metadata-from-file startup-script=./gcloud_blockchain_hbc1.sh \
    --zone=us-central1-a

echo "Done!"
