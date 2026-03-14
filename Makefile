.PHONY: install test clean lint format dev-install uninstall help

help:
	@echo "Kimi Enterprise - Available commands:"
	@echo "  make install      - Install system-wide"
	@echo "  make dev-install  - Install in development mode"
	@echo "  make test         - Run test suite"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make uninstall    - Remove installation"

install:
	./install.sh

dev-install:
	pip install -e .

test:
	python -m pytest tests/ -v

lint:
	flake8 lib/kimi_enterprise --max-line-length=100
	pylint lib/kimi_enterprise

format:
	black lib/kimi_enterprise
	isort lib/kimi_enterprise

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyc" -delete

uninstall:
	rm -rf ~/.kimi-enterprise
	pip uninstall kimi-enterprise -y
