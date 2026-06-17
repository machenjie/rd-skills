.PHONY: quickstart-codex quickstart-codex-dry-run quickstart-claude-project quickstart-copilot-project doctor-codex

quickstart-codex:
	python3 scripts/quickstart.py --agent codex --scope user

quickstart-codex-dry-run:
	python3 scripts/quickstart.py --agent codex --scope user --dry-run

quickstart-claude-project:
ifndef TARGET
	$(error TARGET is required, e.g. make quickstart-claude-project TARGET=/path/to/project)
endif
	python3 scripts/quickstart.py --agent claude --scope project --target $(TARGET)

quickstart-copilot-project:
ifndef TARGET
	$(error TARGET is required, e.g. make quickstart-copilot-project TARGET=/path/to/project)
endif
	python3 scripts/quickstart.py --agent copilot --scope project --target $(TARGET)

doctor-codex:
	python3 installers/doctor.py --agent codex --scope user --profile recommended
