DOCKER_IMAGE = symphox-apollo:latest
WORKDIR = /app

UID = $(shell id -u)
GID = $(shell id -g)
TTY_SUPPORT ?= t

DOCKER_WORKDIR = -w $(WORKDIR)
DOCKER_MOUNT = --mount type=bind,src=$(PWD),target=$(WORKDIR)
DOCKER_USER = -u $(UID):$(GID)

build:
	docker build -t $(DOCKER_IMAGE) .

--run:
	docker run --rm -i$(TTY_SUPPORT) \
        $(DOCKER_WORKDIR) \
        $(DOCKER_MOUNT) \
        $(DOCKER_USER) \
        $(DOCKER_IMAGE) \
        $(CMD)

shell: CMD = bash
shell: --run
