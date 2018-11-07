.PHONY:	build push dev

PREFIX = hub.bccvl.org.au/ecocloud
IMAGE = ecocloud_wps_demo
TAG ?= 0.0.2

build:
	docker build -t $(PREFIX)/$(IMAGE):$(TAG) .

dev:
	docker run --rm -it -p 6543:6543 -v $(PWD):/code $(PREFIX)/$(IMAGE):$(TAG) bash

push:
	docker push $(PREFIX)/$(IMAGE):$(TAG)

run:
	docker run --rm -it -v $(PWD):/code -p 6543:6543 $(PREFIX)/$(IMAGE):$(TAG)
