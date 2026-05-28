.PHONY: help install test run run-dev clean lint format type-check

help:
	@echo "GardRail Development Tasks"
	@echo "=========================="
	@echo "make install      - Install dependencies in virtual environment"
	@echo "make install-dev  - Install dependencies + dev tools"
	@echo "make run          - Run production server"
	@echo "make run-dev      - Run development server with auto-reload"
	@echo "make test         - Run test suite"
	@echo "make test-cov     - Run tests with coverage report"
	@echo "make lint         - Check code style (flake8)"
	@echo "make format       - Format code with black"
	@echo "make type-check   - Check types with mypy"
	@echo "make clean        - Remove cache and build files"
	@echo "make demo         - Run demo scenarios"

install:
	python -m venv venv
	. venv/bin/activate && pip install -q -r requirements.txt
	@echo "✓ Dependencies installed in ./venv"
	@echo "  Run: source venv/bin/activate"

install-dev: install
	. venv/bin/activate && pip install -q pytest-watch black flake8 mypy
	@echo "✓ Development tools installed"

run:
	. venv/bin/activate && uvicorn api.server:app --host 0.0.0.0 --port 8000

run-dev:
	. venv/bin/activate && uvicorn api.server:app --reload --host 127.0.0.1 --port 8000

test:
	. venv/bin/activate && pytest -v

test-cov:
	. venv/bin/activate && pytest --cov=core --cov=api --cov=db --cov-report=html

test-watch:
	. venv/bin/activate && ptw

lint:
	. venv/bin/activate && flake8 core/ api/ agent/ db/ tests/ --max-line-length=88

format:
	. venv/bin/activate && black core/ api/ agent/ db/ tests/ examples/

type-check:
	. venv/bin/activate && mypy core/ api/ agent/ db/ --ignore-missing-imports

demo:
	. venv/bin/activate && python demo.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	@echo "✓ Cache and build files cleaned"

.DEFAULT_GOAL := help
