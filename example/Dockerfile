FROM henritel/git-blog AS builder

COPY . /blog
RUN git-blog

FROM nginx:1.23-alpine
COPY media /usr/share/nginx/html/media/
COPY --from=builder /out/blog/ /usr/share/nginx/html
