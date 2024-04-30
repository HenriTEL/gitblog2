FROM python:3.12-slim

ARG GITBLOG2_VERSION

# ADD https://deb.nodesource.com/setup_16.x /tmp/setup_nodejs_16
# RUN bash /tmp/setup_nodejs_16
RUN apt-get update \
	&& apt-get install -y zip git
# && apt install -y nodejs \
# && npm install -g wrangler purgecss postcss-cli autoprefixer cssnano
RUN pip3 install --no-cache-dir gitblog2==${GITBLOG2_VERSION}

COPY providers/ /providers

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
