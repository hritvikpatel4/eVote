FROM python

LABEL maintainer="Hritvik Patel <hritvik.patel4@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /usr/src/app/logs

RUN apt update \
    && apt install -y git

WORKDIR /usr/src/app

RUN git clone https://github.com/hritvikpatel4/eVote.git
RUN cd eVote && git checkout dev && cd webserver && pip install -r requirements.txt

EXPOSE 80

CMD ["sh", "-c", "python eVote/webserver/webserver.py"]