# Makefile for Open-Mon asset pipeline
# Needs cairosvg: pip install -e .[tools]
# Audio is generated in code (src/engine/audio.py); nothing to build here.

PYTHON ?= python
MASCOTS := $(basename $(notdir $(wildcard mascots/*.svg)))
OVERWORLD := $(basename $(notdir $(wildcard mascots/overworld/*.svg)))
PNGS := $(MASCOTS:%=assets/sprites/%.png) $(OVERWORLD:%=assets/sprites/overworld/%.png)

assets: $(PNGS)

assets/sprites/%.png: mascots/%.svg scripts/svg2gb.py
	@mkdir -p $(dir $@)
	$(PYTHON) scripts/svg2gb.py $< $@ 32

assets/sprites/overworld/%.png: mascots/overworld/%.svg scripts/svg2gb.py
	@mkdir -p $(dir $@)
	$(PYTHON) scripts/svg2gb.py $< $@ 8

.PHONY: assets

# One-time setup: use the tracked git hooks (.githooks/pre-push mirrors CI)
hooks:
	git config core.hooksPath .githooks

.PHONY: hooks
