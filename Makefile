PYDOCTOR=pydoctor

test:
	trial kademlia

lint:
	pep8 --ignore=E303,E251,E201,E202 ./kademlia --max-line-length=140
	find ./kademlia -name '*.py' | xargs pyflakes

install:
	python setup.py install
