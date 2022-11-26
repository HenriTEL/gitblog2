FROM nikolaik/python-nodejs:python3.11-nodejs19-slim

RUN npm install -g npm wrangler
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY main.py .
COPY media media
COPY css css
COPY templates templates
COPY providers providers

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]