# Phoenix_aston_cheats — regenerate, verify and package the installable tree
PY ?= python3
STOCK := reference/stock
MOD := Phoenix_aston_cheats

.PHONY: all port check test verify-package package check-strings clean

all: port check test verify-package

port:
	$(PY) tools/port_to_phoenix.py --from stock $(STOCK)/r6/tweaks/xaires/aston_valkyrie.yaml \
		--out $(MOD)/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml
	$(PY) tools/port_to_phoenix.py --from stock $(STOCK)/r6/scripts/xaires_aston_valkyrie \
		--out $(MOD)/r6/scripts/phoenix_aston_valkyrie

check:
	$(PY) tools/port_to_phoenix.py --check $(MOD)

test:
	$(PY) -m unittest discover -s tests -v

# game-root mirror, no docs junk, archive + .xl paired, tweaks/scripts in subfolders
verify-package:
	$(PY) tools/package.py --check --mod $(MOD)

# Nexus upload: dist/Phoenix_aston_cheats.zip
package: port check verify-package
	$(PY) tools/package.py --mod $(MOD) --zip

# after the WolvenKit step: the strings archive must carry the path the .xl names
check-strings:
	$(PY) tools/inspect_archive.py $(MOD)/archive/pc/mod/phoenix_strings.archive \
		--json-only --expect 'phoenix\aston_valkyrie\en-us.json'

clean:
	rm -rf $(MOD)/r6 dist tools/__pycache__ tests/__pycache__
