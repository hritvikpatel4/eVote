FROM python:3.8

LABEL maintainer="Hritvik Patel <hritvik.patel4@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /usr/src/app/logs

RUN apt update \
    && apt install -y git

WORKDIR /usr/src/app

RUN git clone https://github.com/hritvikpatel4/eVote.git \
    && cd eVote && git checkout dev && rm -rf dbserver && rm -f *.sh *.json *.py *.md *.txt \
    && rm -rf Blockchain && rm -rf bc && rm -rf orderer && rm -rf load_balancer && rm -rf timer \
    && cd webserver && pip install -r requirements.txt

COPY capstone-304713.json /usr/src/app/eVote/webserver

EXPOSE 80

CMD ["sh", "-c", "cd eVote/webserver && gunicorn --log-level debug webserver"]
# CMD ["sh", "-c", "cd eVote/webserver && gunicorn --log-level debug wsgi:application"]