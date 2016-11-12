test: build/venv
	@( . build/venv/bin/activate; \
	    cd src && \
	    coverage erase && \
		nosetests --with-xunit --xunit-file=../build/nosetests.xml \
			--with-coverage --cover-package=spacel --cover-xml --cover-xml-file=../build/coverage.xml \
			test \
	)

lint: build/venv
	@( . build/venv/bin/activate; \
		find src -not -path 'src/test*' -name '*.py' | xargs pylint --rcfile pylintrc \
	)

clean:
	rm -Rf build/

build/venv: build/venv/bin/activate

build/venv/bin/activate: requirements.txt
	@mkdir -p build
	@test -d build/venv || virtualenv -p python3 build/venv
	@( . build/venv/bin/activate;  \
		pip install -r requirements.txt; \
		pip install -r src/test/requirements.txt; \
	)

composetest:
	-docker-compose kill
	-docker-compose rm -f
	docker-compose build
	docker-compose run --rm test
	docker-compose run --rm test-python2


# Adjust this to execute a single integration test:
test_integ_one: build/venv
	@( . build/venv/bin/activate; \
		cd src && \
		LAMBDA_BUCKET=spacel-pebbledev \
		LAMBDA_REGION=us-east-1 \
		nosetests --with-xunit --xunit-file=../build/nosetests-integration.xml \
		test_integ.test_deploy:TestDeploy.test_01_deploy_simple_http \
	)

.PHONY: composetest test test_integ_one lint
