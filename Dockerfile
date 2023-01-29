FROM python:3.11-alpine

ARG GITBLOG2_VERSION

ENV APK_BUILD_DEPS="gcc musl-dev libgit2-dev"

RUN apk add --update nodejs npm zip ${APK_BUILD_DEPS} \
	&& npm install -g wrangler purgecss postcss-cli autoprefixer cssnano \
	&& pip3 install --no-cache-dir gitblog2==${GITBLOG2_VERSION} \
	&& apk del ${APK_BUILD_DEPS} \
	&& rm -rf /var/cache/apk/*

COPY providers /providers

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
