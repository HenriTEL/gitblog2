# Development quickstart

Make sure to have [poetry](https://python-poetry.org/) installed, then  
Setup your local web server:

```bash
poetry install
wget "https://redbean.dev/redbean-tiny-2.2.com" -O redbean.zip
zip redbean.zip -j providers/assets/.init.lua
chmod +x redbean.zip
```

In one terminal, update the blog as needed:

```bash
poetry run gitblog2 -l debug --repo-subdir=example --base-url=https://example.com --no-social
```

In another terminal, serve the blog:

```bash
./redbean.zip -D ./public
```
