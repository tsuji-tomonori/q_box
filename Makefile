dev_init:
	pip install -r requirements-dev.txt

check:
	flake8 src/
	mypy src/
	black src/

local_test:
	python -m pytest \
		--cov==src \
		--cov-report html:reports/

deploy:
	pip install -r requirements-deploy.txt
	cdk deploy