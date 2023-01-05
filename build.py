# Merge css files into gitblog2/style.css
with open("gitblog2/style.css", "w") as dest:
    for f in ("css/layout.css", "css/style.css"):
        with open(f, "r") as src:
            dest.write(src.read())
