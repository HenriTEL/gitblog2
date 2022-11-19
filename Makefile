.PHONY: redbean.zip clean


serve: redbean.zip
	./redbean.zip -D www/


redbean.zip: redbean.com
	cp redbean.com redbean.zip
	zip redbean.zip .init.lua
	chmod +x redbean.zip
	CLONE_PATH=. REPO_SUBDIR=example/ ./main.py
	cd www; zip -r redbean.zip .; cd -


redbean.com:
	wget https://redbean.dev/redbean-unsecure-2.2.com --output-document=redbean.com


clean:
	rm redbean.*