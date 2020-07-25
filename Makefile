.PHONY: activate build clean compile deactivate install run test

SHELL := /bin/bash

activate:
	conda activate hummingbot

build:
	python setup.py build_ext --inplace

clean:
	./clean

compile:
	./compile

deactivate:
	echo "My current shell - $(SHELL)"
	conda init bash
	#conda deactivate

install:
	./install

run:
	bin/hummingbot.py

test: clean install deactivate activate build
	nosetests -d -v test/test*.py
