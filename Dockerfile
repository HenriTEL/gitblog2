FROM python:3.11-slim

ARG GITBLOG2_VERSION

RUN apt update \
	&& apt install -y nodejs npm zip libgit2-dev gcc \
	&& npm install -g wrangler purgecss postcss-cli autoprefixer cssnano
RUN pip3 install --no-cache-dir gitblog2==${GITBLOG2_VERSION}

COPY providers/ /providers

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
