PYTHON ?= python

ifeq ($(OS),Windows_NT)
VENV_PYTHON = .venv/Scripts/python.exe
else
VENV_PYTHON = .venv/bin/python
endif

MANAGE = $(VENV_PYTHON) manage.py

.PHONY: help deps run migrate makemigrations test lint format up down logs

help:
	@echo "deps             Install dependencies"
	@echo "run              Apply migrations and start the API"
	@echo "migrate          Apply migrations"
	@echo "makemigrations   Create migrations"
	@echo "test             Run tests"
	@echo "lint / format    Check or format Python code"
	@echo "up / down / logs Docker Compose commands"

$(VENV_PYTHON):
	$(PYTHON) -m venv .venv

deps: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pip install -r requirements.txt ruff==0.16.6

run: migrate
	$(MANAGE) runserver

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

test:
	$(MANAGE) test events

lint:
	$(VENV_PYTHON) -m ruff check .
	$(VENV_PYTHON) -m ruff format --check .

format:
	$(VENV_PYTHON) -m ruff format .

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f web
