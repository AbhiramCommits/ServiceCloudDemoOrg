PYTHON ?= python

.PHONY: all data sim eval test clean

## Run the entire reproducible pipeline from clean: generate data, run both
## scenarios, evaluate the assistant, then run the test suite.
all: clean data sim eval test

## Generate the deterministic synthetic dataset (data/orders.csv, data/requests_baseline.csv).
data:
	$(PYTHON) data/generate_data.py

## Run the BASELINE vs SALESFORCE simulation and write results/metrics.json + metrics.md.
sim: data
	$(PYTHON) -m sim.run_simulation --out results/

## Evaluate the deflection assistant and write results/assistant_eval.json + confusion_matrix.md.
eval: data
	$(PYTHON) -m sim.eval_assistant --out results/

## Run the pytest suite.
test:
	$(PYTHON) -m pytest -q

## Remove generated results so `make all` proves the pipeline is reproducible from clean.
clean:
	rm -rf results
