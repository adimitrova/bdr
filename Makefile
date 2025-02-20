install:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip3 install -r requirements.txt
run:
	export PYSPARK_PYTHON=venv/bin/python
	export SPARK_HOME=venv/lib/python3.12/site-packages/pyspark
	venv/bin/python3 -m main
clean:
	rm -rf venv/
build:
# 	docker build --progress=plain --no-cache -t bdr-app .
	docker-compose build
run_with_docker:
	docker-compose up
test:
	venv/bin/python -m pytest test/