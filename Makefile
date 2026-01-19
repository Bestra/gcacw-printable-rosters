# GCACW Scenario Parser - Build Pipeline
#
# Data flow:
#   PDF → raw_table_extractor.py → raw/{game}_raw_tables.json  (manual step)
#   raw tables + game_configs.json → parse_raw_tables.py → parsed/{game}_parsed.json
#   parsed JSON → convert_to_web.py → web/public/data/{game}.json
#
# Usage:
#   make              - Build all web JSON files (default)
#   make parsed       - Build all parsed JSON files
#   make clean        - Remove generated files
#   make dev          - Start the dev server
#   make build        - Build the web app for production

SHELL := /bin/bash

# All games
ALL_GAMES := gtc2 hcr hsn otr2 rtg2 rwh tom tpc aga sjw

# Directories
PARSER_DIR := parser
WEB_DATA_DIR := web/public/data
WEB_SRC_DATA_DIR := web/src/data
RAW_DIR := $(PARSER_DIR)/raw
PARSED_DIR := $(PARSER_DIR)/parsed
IMAGE_MAPPINGS_DIR := $(PARSER_DIR)/image_mappings

# Python command (using uv)
PYTHON := cd $(PARSER_DIR) && uv run python

# Generated files (raw files are treated as source, not auto-generated)
PARSED_FILES := $(patsubst %,$(PARSED_DIR)/%_parsed.json,$(ALL_GAMES))
WEB_FILES := $(patsubst %,$(WEB_DATA_DIR)/%.json,$(ALL_GAMES))

# =============================================================================
# Main targets
# =============================================================================

.PHONY: all
all: web

# Build all web JSON files
.PHONY: web
web: $(WEB_FILES) $(WEB_DATA_DIR)/games.json copy-image-mappings

# Build all parsed JSON files
.PHONY: parsed
parsed: $(PARSED_FILES)

# =============================================================================
# Pattern rules for the pipeline
# =============================================================================

# parsed/{game}_parsed.json depends on raw tables and parser config
$(PARSED_DIR)/%_parsed.json: $(RAW_DIR)/%_raw_tables.json $(PARSER_DIR)/game_configs.json $(PARSER_DIR)/pipeline/parse_raw_tables.py
	@echo "Parsing $*..."
	$(PYTHON) pipeline/parse_raw_tables.py $*

# web/public/data/{game}.json depends on parsed data
$(WEB_DATA_DIR)/%.json: $(PARSED_DIR)/%_parsed.json $(PARSER_DIR)/pipeline/convert_to_web.py
	@echo "Converting $* to web format..."
	$(PYTHON) pipeline/convert_to_web.py $*

# games.json is regenerated when convert_to_web.py changes
$(WEB_DATA_DIR)/games.json: $(PARSER_DIR)/pipeline/convert_to_web.py
	@echo "Regenerating games.json..."
	$(PYTHON) pipeline/convert_to_web.py

# Copy image mapping JSON files to web/src/data for TypeScript imports
# Note: Image mappings may be in parser/image_mappings/ or parser/image_extraction/image_mappings/
.PHONY: copy-image-mappings
copy-image-mappings:
	@echo "Copying image mappings to web/src/data..."
	@cp -f $(IMAGE_MAPPINGS_DIR)/*_images.json $(WEB_SRC_DATA_DIR)/ 2>/dev/null || true
	@cp -f $(PARSER_DIR)/image_extraction/image_mappings/*_images.json $(WEB_SRC_DATA_DIR)/ 2>/dev/null || true

# =============================================================================
# Convenience targets
# =============================================================================

# Build a single game: make gtc2, make otr2, etc.
.PHONY: $(ALL_GAMES)
$(ALL_GAMES): %: $(WEB_DATA_DIR)/%.json

# Force reparse a game (delete parsed + web, then rebuild)
.PHONY: reparse-%
reparse-%:
	@echo "Force reparsing $*..."
	rm -f $(PARSED_DIR)/$*_parsed.json $(WEB_DATA_DIR)/$*.json
	$(MAKE) $(WEB_DATA_DIR)/$*.json

# =============================================================================
# PDF extraction (manual step - run explicitly when needed)
# =============================================================================

# Extract raw tables from a PDF: make extract-gtc2
# Uses environment variables from parser/.env:
#   {GAME}_RULES_PATH (e.g., GTC2_RULES_PATH)
# Requires environment variable to be set - no fallback.
.PHONY: extract-%
extract-%:
	@echo "Extracting raw tables for $*..."
	$(PYTHON) pipeline/raw_table_extractor.py $*

# =============================================================================
# Clean targets
# =============================================================================

.PHONY: clean
clean:
	rm -f $(PARSED_FILES)
	rm -f $(WEB_FILES)
	rm -f $(WEB_DATA_DIR)/games.json

.PHONY: rebuild
rebuild: clean all

# =============================================================================
# Development
# =============================================================================

.PHONY: dev
dev:
	cd web && npm run dev

.PHONY: build
build: web
	cd web && npm run build

.PHONY: test
test:
	@echo "Running parser tests..."
	cd $(PARSER_DIR) && uv run pytest tests/ -v
	@echo ""
	@echo "Running web tests..."
	cd web && npm test

# =============================================================================
# LLM Evaluation
# =============================================================================

# Generate DOM snapshots for all games
.PHONY: snapshots
snapshots:
	cd web && npm run snapshots

# Generate snapshot for a single game: make snapshots-game GAME=gtc2
.PHONY: snapshots-game
snapshots-game:
	cd web && SNAPSHOT_GAME=$(GAME) npm run snapshots

# Generate snapshot for a single scenario: make snapshots-single GAME=gtc2 SCENARIO=1
.PHONY: snapshots-single
snapshots-single:
	cd web && SNAPSHOT_GAME=$(GAME) SNAPSHOT_SCENARIO=$(SCENARIO) npm run snapshots

# Run LLM evaluation for all games
.PHONY: llm-eval
llm-eval: snapshots
	cd web && npm run llm-eval

# Run LLM evaluation for a single scenario: make llm-eval-single GAME=gtc2 SCENARIO=1
.PHONY: llm-eval-single
llm-eval-single: snapshots-single
	cd web && npx tsx scripts/llm-eval.ts --game $(GAME) --scenario $(SCENARIO)

# =============================================================================
# Help
# =============================================================================

.PHONY: help
help:
	@echo "GCACW Scenario Parser - Build Targets"
	@echo ""
	@echo "Main targets:"
	@echo "  make              - Build all web JSON files (default)"
	@echo "  make web          - Build all web JSON files"
	@echo "  make parsed       - Build all parsed JSON files"
	@echo ""
	@echo "Individual games:"
	@echo "  make gtc2         - Build Grant Takes Command"
	@echo "  make hcr          - Build Here Come the Rebels"
	@echo "  make hsn          - Build Hood Strikes North"
	@echo "  make otr2         - Build On To Richmond"
	@echo "  make rtg2         - Build Roads to Gettysburg 2"
	@echo "  make rwh          - Build Rebels in the White House"
	@echo "  make tom          - Build Thunder on the Mississippi"
	@echo ""
	@echo "Rebuild targets:"
	@echo "  make reparse-GAME - Force reparse (e.g., make reparse-otr2)"
	@echo "  make rebuild      - Clean and rebuild everything"
	@echo ""
	@echo "PDF extraction (manual step):"
	@echo "  make extract-GAME - Extract raw tables from PDF"
	@echo "                      (e.g., make extract-gtc2)"
	@echo ""
	@echo "LLM evaluation:"
	@echo "  make snapshots    - Generate DOM snapshots for all games"
	@echo "  make snapshots-game GAME=gtc2"
	@echo "                    - Generate snapshots for a single game"
	@echo "  make snapshots-single GAME=gtc2 SCENARIO=1"
	@echo "                    - Generate snapshot for single scenario"
	@echo "  make llm-eval     - Run LLM evaluation for all games"
	@echo "  make llm-eval-single GAME=gtc2 SCENARIO=1"
	@echo "                    - Run LLM evaluation for single scenario"
	@echo ""
	@echo "Other targets:"
	@echo "  make dev          - Start development server"
	@echo "  make build        - Build web app for production"
	@echo "  make test         - Run all tests (parser + web)"
	@echo "  make clean        - Remove parsed and web JSON files"
	@echo "  make help         - Show this help"
