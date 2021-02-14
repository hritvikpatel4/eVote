FROM python

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /usr/src/app
COPY . .

EXPOSE 8080

RUN mkdir -p /usr/src/app/logs && pip install -r requirements.txt
CMD ["sh", "-c", "python load_balancer.py"]