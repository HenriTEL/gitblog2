FROM nikolaik/python-nodejs:python3.11-nodejs19-slim

RUN apt update \
	&& apt install -y zip \
	&& rm -rf /var/lib/apt/lists/*
RUN npm install -g npm wrangler purgecss postcss-cli autoprefixer cssnano
RUN pip3 install gitblog2==0.2.3

COPY providers /providers

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]