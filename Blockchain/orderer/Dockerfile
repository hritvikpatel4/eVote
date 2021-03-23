FROM python:3.8

LABEL maintainer="Hritvik Patel <hritvik.patel4@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /usr/src/app/logs

RUN apt update \
    && apt install -y git

WORKDIR /usr/src/app

RUN git clone https://github.com/hritvikpatel4/eVote.git \
    && cd eVote && git checkout dev && rm -rf webserver && rm -rf dbserver && rm -f *.sh *.json *.py *.md *.txt \
    && rm -rf Blockchain/bc && rm -rf Blockchain/load_balancer && rm -f Blockchain/*.py \
    && cd Blockchain/orderer && pip install -r requirements.txt

EXPOSE 80

CMD ["sh", "-c", "cd eVote/Blockchain && gunicorn orderer.wsgi:application"]