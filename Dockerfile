FROM alpine
ENV REPO_URL https://example.git
ENV OUTPUT_DIR /html

RUN apk --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community add git gomplate cmark

COPY main.sh /
CMD ["/main.sh"]