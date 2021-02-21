FROM python

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /usr/src/app
COPY . .

EXPOSE 80

RUN mkdir -p /usr/src/app/logs && pip install -r requirements.txt
CMD ["sh", "-c", "python bc.py"]