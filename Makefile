.PHONY:	build push dev

PREFIX = hub.bccvl.org.au/ecocloud
IMAGE = ecocloud_wps_demo
TAG ?= 0.0.4
VOLUMES = -v $(PWD)/pywps.cfg:/etc/ecocloud/pywps.cfg
VOLUMES += -v $(PWD)/development.ini:/etc/ecocloud/wps.ini
PORTS = -p 6543:6543

build:
	docker build -t $(PREFIX)/$(IMAGE):$(TAG) .

dev:
	docker run --rm -it $(PORTS) $(VOLUMES) $(PREFIX)/$(IMAGE):$(TAG) bash

push:
	docker push $(PREFIX)/$(IMAGE):$(TAG)

run:
	docker run --rm -it $(PORTS) $(VOLUMES) $(PREFIX)/$(IMAGE):$(TAG)
