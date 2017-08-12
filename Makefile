PYTHON=python2.7

ENV_DIR=.env_$(PYTHON)

ifeq ($(OS),Windows_NT)
	IN_ENV=. $(ENV_DIR)/Scripts/activate &&
else
	IN_ENV=. $(ENV_DIR)/bin/activate &&
endif

all: test lint docs sdist

env: $(ENV_DIR)
	$(IN_ENV) pip install -U pip

test: build
	$(IN_ENV) nosetests -v --with-xunit --xunit-file=test_results.xml --with-coverage --cover-erase --cover-xml  --cover-package=htmldiff

# Quick test invoke
qt:
	$(IN_ENV) nosetests -v --with-xunit --xunit-file=test_results.xml --with-coverage --cover-erase --cover-xml  --cover-package=htmldiff

artifacts: build sdist

$(ENV_DIR):
	virtualenv -p $(PYTHON) $(ENV_DIR)

build_reqs: env
	$(IN_ENV) pip install sphinx pep8 coverage nose unify

build: build_reqs
	$(IN_ENV) pip install --editable .

sdist: build
	$(IN_ENV) python setup.py sdist

unify: build_reqs
	- $(IN_ENV) unify --in-place --recursive src/

lint: pep8

pep8: build_reqs
	- $(IN_ENV) pep8 src/htmldiff > pep8.out

docs: build
	$(IN_ENV) pip install -r docs/requirements.txt
	$(IN_ENV) $(MAKE) -C docs html

freeze: env
	- $(IN_ENV) pip freeze

shell: env
	- $(IN_ENV) $(PYTHON)

clean:
	- @rm -rf BUILD
	- @rm -rf BUILDROOT
	- @rm -rf RPMS
	- @rm -rf SRPMS
	- @rm -rf SOURCES
	- @rm -rf docs/build
	- @rm -rf src/*.egg-info
	- @rm -rf build
	- @rm -rf dist
	- @rm -rf docs/_build
	- @rm -rf docs/build
	- @rm -f .coverage
	- @rm -f test_results.xml
	- @rm -f coverage.xml
	- @rm -f pep8.out
	- find -name '*.pyc' -delete
	- find -name '*.pyo' -delete
	- find -name '*.pyd' -delete

env_clean: clean
	- @rm -rf $(ENV_DIR)
