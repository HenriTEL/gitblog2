# Git-blog

git + Markdown = blog

## TODO

* Live update locally
* Generate index.html
* Rebuild when repo updates by default
* Nginx config `try_files $uri $uri.html $uri/index.html =404;`
* Draft support (gen blacklist + set publish_date to first `mv`)

## Development

You can lively check your local changes by running the following commands in 2 separate terminals:
```bash
# In one terminal, lively rebuild based on local changes
./ live-build.sh

# In another terminal, serve the blog locally
docker run -v "${PWD}/.out/blog":/usr/share/nginx/html:ro -p 127.0.0.1:8080:80 nginx:alpine
```

Reload <http://127.0.0.1:8080/articles/example.html> to check the results.