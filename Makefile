PYDOCTOR=pydoctor

test:
	trial kademlia

docs:
	$(PYDOCTOR) --make-html --html-output apidoc --add-package kademlia --project-name=kademlia --project-url=http://github.com/bmuller/kademlia --html-use-sorttable --html-use-splitlinks --html-shorten-lists 

lint:
	pep8 --ignore=E303,E251,E201,E202 ./kademlia --max-line-length=140
	find ./kademlia -name '*.py' | xargs pyflakes

install:
	python setup.py install
