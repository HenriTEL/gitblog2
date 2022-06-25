FROM alpine
ENV REPO_URL
ENV OUTPUT_DIR

RUN apk --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community add git gomplate cmark

COPY main.sh /
CMD ["/main.sh"]