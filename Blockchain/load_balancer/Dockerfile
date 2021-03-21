FROM python

LABEL maintainer="Hritvik Patel <hritvik.patel4@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /usr/src/app/logs

RUN apt update \
    && apt install -y git

WORKDIR /usr/src/app

RUN git clone https://github.com/hritvikpatel4/eVote.git
RUN cd eVote && git checkout dev && cd Blockchain/load_balancer && pip install -r requirements.txt
RUN cd eVote && rm -rf webserver && rm -rf databaseserver && rm -f *.sh *.json *.py *.md *.txt
RUN cd eVote && rm -rf Blockchain/bc && rm -rf Blockchain/orderer && rm -f Blockchain/*.py

EXPOSE 80

CMD ["sh", "-c", "python eVote/Blockchain/load_balancer/load_balancer.py"]