.PHONY: install test hygiene check generate validate volume clean-local

PYTHON ?= python3
CONFIG ?= config/scenario.yaml
COHORT ?= data/cohort
OUTPUT ?= generated

install:
	$(PYTHON) -m pip install -r generator/requirements.txt -r requirements-dev.txt

test:
	$(PYTHON) -m pytest

hygiene:
	$(PYTHON) scripts/check_repo.py

check: test hygiene

generate:
	$(PYTHON) generator/generate.py --config $(CONFIG) --cohort $(COHORT) --output $(OUTPUT)

validate:
	$(PYTHON) generator/validate.py --config $(CONFIG) --cohort $(COHORT) --output $(OUTPUT)

volume:
	$(PYTHON) scripts/estimate_volume.py --output $(OUTPUT)

clean-local:
	$(PYTHON) scripts/clean_local.py --output $(OUTPUT)
