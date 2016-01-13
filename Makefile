PY_VERSION := 3
WHEEL_DIR := /tmp/wheelhouse
PIP := env/bin/pip
PY := env/bin/python
USE_WHEELS := 0
ifeq ($(USE_WHEELS), 0)
  WHEEL_INSTALL_ARGS := # void
else
  WHEEL_INSTALL_ARGS := --use-wheel --no-index --find-links=$(WHEEL_DIR)
endif


help:
	@echo "COMMANDS:"
	@echo "  clean          Remove all generated files."
	@echo "  setup          Setup development environment."
	@echo "  shell          Open ipython from the development environment."
	@echo "  test           Run tests."
	@echo "  lint           Run analysis tools."
	@echo "  wheel          Build package wheel & save in $(WHEEL_DIR)."
	@echo "  wheels         Build dependency wheels & save in $(WHEEL_DIR)."
	@echo "  publish        Build and upload package to pypi.python.org"
	@echo ""
	@echo "VARIABLES:"
	@echo "  PY_VERSION     Version of python to use. 2 or 3"
	@echo "  WHEEL_DIR      Where you save your wheels. Default: $(WHEEL_DIR)."
	@echo "  USE_WHEELS     Install packages from wheel dir, off by default."


clean:
	rm -rf env
	rm -rf build
	rm -rf dist
	rm -rf *.egg
	rm -rf *.egg-info
	find | grep -i ".*\.pyc$$" | xargs -r -L1 rm


virtualenv: clean
	virtualenv -p /usr/bin/python$(PY_VERSION) env
	$(PIP) install wheel


wheels: virtualenv
	$(PIP) wheel --find-links=$(WHEEL_DIR) --wheel-dir=$(WHEEL_DIR) -r requirements.txt
	$(PIP) wheel --find-links=$(WHEEL_DIR) --wheel-dir=$(WHEEL_DIR) -r test_requirements.txt


wheel: test
	$(PY) setup.py bdist_wheel
	mv dist/*.whl $(WHEEL_DIR)


setup: virtualenv
	$(PIP) install $(WHEEL_INSTALL_ARGS) -r requirements.txt
	$(PIP) install $(WHEEL_INSTALL_ARGS) -r test_requirements.txt


shell: setup
	env/bin/ipython


test: setup
	$(PY) setup.py test


install: test
	$(PY) setup.py install


server: setup
	$(PY) examples/server.py


publish: test
	$(PY) setup.py register bdist_wheel upload


lint: test
	pep8 --ignore=E303,E251,E201,E202 ./kademlia --max-line-length=140
	find ./kademlia -name '*.py' | xargs pyflakes


# Break in case of bug!
# import pudb; pu.db
