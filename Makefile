IMAGE ?= localhost/pysigma-api:latest
PORT ?= 8001

.PHONY: test build run clean

test:
	pytest -q

build:
	podman build -t $(IMAGE) .

run:
	podman run --rm --name pysigma-api -p $(PORT):8000 $(IMAGE)

clean:
	rm -rf .pytest_cache app/__pycache__ tests/__pycache__
