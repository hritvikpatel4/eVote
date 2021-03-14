FROM python

LABEL maintainer="Hritvik Patel <hritvik.patel4@gmail.com>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt update \
    && apt install -y git

WORKDIR /usr/src/app

RUN git clone https://github.com/hritvikpatel4/eVote.git
RUN cd eVote && git checkout dev
RUN mkdir -p /usr/src/app/logs && pip install -r webserver/requirements.txt

EXPOSE 80

CMD ["sh", "-c", "python webserver/webserver.py"]