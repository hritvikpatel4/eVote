FROM python:3.8

LABEL maintainer="Hritvik Patel <hritvik.patel4@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /usr/src/app/logs

RUN apt update \
    && apt install -y git \
    && curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-334.0.0-linux-x86_64.tar.gz > /tmp/gcloud-sdk.tar.gz \
    && mkdir -p /usr/local/gcloud \
    && tar -C /usr/local/gcloud -xvf /tmp/gcloud-sdk.tar.gz \
    && /usr/local/gcloud/google-cloud-sdk/install.sh --quiet

ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin
COPY capstone-304713.json /tmp
RUN gcloud auth activate-service-account capstone-service@capstone-304713.iam.gserviceaccount.com --key-file=/tmp/capstone-304713.json --project=capstone-304713
RUN cd /tmp && rm -f capstone-304713.json gcloud-sdk.tar.gz

WORKDIR /usr/src/app

COPY github_key .
RUN eval $(ssh-agent) \
    && ssh-add github_key \
    && ssh-keyscan -H github.com >> /etc/ssh/ssh_known_hosts \
    && git clone git@github.com:hritvikpatel4/eVote.git \
    && cd eVote && git checkout dev && rm -rf dbserver && rm -f *.sh *.json *.py *.md *.txt \
    && rm -rf Blockchain && rm -rf bc && rm -rf orderer && rm -rf load_balancer && rm -rf timer && rm -rf eVote-spark && rm -rf async_requests \
    && cd webserver && pip install -r requirements.txt

RUN rm -f github_key && rm -rf /etc/ssh && rm -rf ~/.ssh
COPY capstone-304713.json /usr/src/app/eVote/webserver
COPY email_creds.txt /tmp

EXPOSE 443

CMD ["sh", "-c", "cd eVote/webserver && gunicorn --log-level debug webserver"]
