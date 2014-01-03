PYDOCTOR=pydoctor

docs:
	$(PYDOCTOR) --make-html --html-output apidoc --add-package rpcudp --project-name=rpcudp --project-url=http://github.com/bmuller/rpcudp --html-use-sorttable --html-use-splitlinks --html-shorten-lists 

lint:
	pep8 --ignore=E303,E251,E201,E202 ./rpcudp --max-line-length=140
	find ./rpcudp -name '*.py' | xargs pyflakes

install:
	python setup.py install
