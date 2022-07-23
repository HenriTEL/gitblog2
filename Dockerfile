FROM alpine

RUN apk --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community add git gomplate cmark
COPY git-blog.sh /bin/git-blog
COPY .gomplate.yaml /
COPY templates /templates
CMD ["git-blog"]