# ![Git-blog Logo](example/media/favicon.svg "title") Git-blog

Git + Markdown = Your blog
Look at cool HTML elements: <https://tapajyoti-bose.medium.com/7-cool-html-elements-nobody-uses-436598d85668>

## TODO

* Add bio and picture from github
* css toolchain like <https://github.com/FullHuman/purgecss/issues/264>
* Live update locally
* Nginx config `try_files $uri $uri.html $uri/index.html =404;`
* Draft support (gen blacklist + set publish_date to first `mv`)

## Internals

Stylesheet is based on water.css

## Development

You can lively check your local changes by running the following commands in 2 separate terminals:

```bash
curl https://redbean.dev/redbean-tiny-2.2.com > redbean.zip
zip redbean.zip .init.lua
./redbean.zip -D www/

# Lively rebuild
./live-build.sh

# Serve the blog
docker run -v "${PWD}/.out/blog":/usr/share/nginx/html:ro -p 127.0.0.1:8080:80 nginx:alpine
```

Reload <http://127.0.0.1:8080/tech> to check the results.
