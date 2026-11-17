.PHONY: test install install-all

test:
	python3 skills/epub-translation-id/tests/test_pipeline.py

install:
	./install.sh

install-all:
	./install.sh --agent all
