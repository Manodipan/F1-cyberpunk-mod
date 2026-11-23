# Phoenix_aston_cheats — regenerate + verify the installable tree
PY ?= python3

.PHONY: all port check test clean

all: port check test

port:
	$(PY) tools/port_to_phoenix.py --from f1 reference/aston_valkyrie_f1.yaml \
		--out Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml
	$(PY) tools/port_to_phoenix.py --from f1 reference/clone_f1 \
		--out Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie

check:
	$(PY) tools/port_to_phoenix.py --check Phoenix_aston_cheats

test:
	$(PY) -m unittest discover -s tests -v

clean:
	rm -rf Phoenix_aston_cheats/r6 tools/__pycache__ tests/__pycache__
