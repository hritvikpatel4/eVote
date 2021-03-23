FROM python

LABEL maintainer="Hritvik Patel <hritvik.patel4@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /usr/src/app/logs

RUN apt update \
    && apt install -y git

WORKDIR /usr/src/app

RUN git clone https://github.com/hritvikpatel4/eVote.git
RUN cd eVote && git checkout dev && cd databaseserver && pip install -r requirements.txt
RUN cd eVote && rm -rf webserver && rm -rf Blockchain && rm -f *.sh *.json *.py *.md *.txt

EXPOSE 80

CMD gunicorn -w 4 --bind 0.0.0.0:$CUSTOM_PORT wsgi