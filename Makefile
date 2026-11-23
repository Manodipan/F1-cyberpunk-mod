# Phoenix_aston_cheats — regenerate + verify the installable tree
PY ?= python3
STOCK := reference/stock

.PHONY: all port check test clean

all: port check test

port:
	$(PY) tools/port_to_phoenix.py --from stock $(STOCK)/r6/tweaks/xaires/aston_valkyrie.yaml \
		--out Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml
	$(PY) tools/port_to_phoenix.py --from stock $(STOCK)/r6/scripts/xaires_aston_valkyrie \
		--out Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie

check:
	$(PY) tools/port_to_phoenix.py --check Phoenix_aston_cheats

test:
	$(PY) -m unittest discover -s tests -v

clean:
	rm -rf Phoenix_aston_cheats/r6 tools/__pycache__ tests/__pycache__
