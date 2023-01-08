import os

# Merge css files into gitblog2/style.css
if os.path.exists("css/"):
    with open("gitblog2/style.css", "w") as dest:
        for f in ("css/layout.scss", "css/style.scss"):
            with open(f, "r") as src:
                dest.write(src.read())
