FROM python:3.8

LABEL maintainer="Hritvik Patel <hritvik.patel4@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /usr/src/app/logs

RUN apt update \
    && apt install -y git

WORKDIR /usr/src/app

COPY github_key .
RUN eval $(ssh-agent) \
    && ssh-add github_key \
    && ssh-keyscan -H github.com >> /etc/ssh/ssh_known_hosts \
    && git clone git@github.com:hritvikpatel4/eVote.git \
    && cd eVote && git checkout dev && rm -rf webserver && rm -rf dbserver && rm -f *.sh *.json *.py *.md *.txt \
    && rm -rf Blockchain && rm -rf bc && rm -rf orderer && rm -rf timer \
    && cd load_balancer && pip install -r requirements.txt

RUN rm -f github_key

EXPOSE 80

CMD ["sh", "-c", "cd eVote/load_balancer && gunicorn --log-level debug load_balancer"]
