FROM python:3.11-alpine

ARG GITBLOG2_VERSION

RUN apk add --update nodejs npm zip gcc musl-dev libgit2-dev
RUN npm install -g wrangler purgecss postcss-cli autoprefixer cssnano
RUN pip3 install gitblog2==${GITBLOG2_VERSION}

COPY providers /providers

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
