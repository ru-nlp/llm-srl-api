# Default recipe to display help information
default:
    @just --list

# Install poetry if not already installed
install-poetry:
    curl -sSL https://install.python-poetry.org | python3 -

# Install all dependencies
install:
    poetry config virtualenvs.in-project true
    poetry install --no-root

# Setup development environment
setup: install-poetry
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f .env ]; then
        cp .env.example .env
    fi
    if ! command -v poetry &> /dev/null; then
        echo "Poetry not found, installing..."
        just install-poetry
    fi
    just install
    # Verify spaCy model installation
    if ! poetry run python -c "import spacy; spacy.load('ru_core_news_lg')" 2>/dev/null; then
        echo "Installing spaCy model..."
        poetry run python -m spacy download ru_core_news_lg
    fi

# Run tests
test:
    PYTHONPATH=. poetry run pytest tests/ -v

# Run tests with coverage report
test-cov:
    PYTHONPATH=. poetry run pytest tests/ -v --cov=app --cov-report=term-missing

# Run tests and watch for changes
test-watch:
    PYTHONPATH=. poetry run ptw tests/ --runner "pytest -v"

# Run the development server with auto-reload
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f .env ]; then
        echo "No .env file found. Running setup first..."
        just setup
    fi
    PYTHONPATH=. poetry run uvicorn app.main:app \
        --reload \
        --host $(grep HOST .env | cut -d '=' -f2) \
        --port $(grep PORT .env | cut -d '=' -f2) \
        --no-access-log \
        --log-level $(grep LOG_LEVEL .env | cut -d '=' -f2 | tr '[:upper:]' '[:lower:]') \
        --reload-delay 0.25

# Run the production server
serve:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f .env ]; then
        echo "No .env file found. Running setup first..."
        just setup
    fi
    PYTHONPATH=. poetry run uvicorn app.main:app \
        --host $(grep HOST .env | cut -d '=' -f2) \
        --port $(grep PORT .env | cut -d '=' -f2) \
        --workers $(grep WORKERS .env | cut -d '=' -f2) \
        --no-access-log \
        --log-level $(grep LOG_LEVEL .env | cut -d '=' -f2 | tr '[:upper:]' '[:lower:]')

# Format code using black and isort
fmt:
    poetry run black .
    poetry run isort .

# Lint code using flake8
lint:
    poetry run flake8 .

# Run formatting and linting
check: fmt lint

# Build Docker image
docker-build:
    docker build -t fastapi-service .

# Run Docker container
docker-run: docker-build
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f .env ]; then
        echo "No .env file found. Creating from example..."
        cp .env.example .env
    fi
    docker run -p $(grep PORT .env | cut -d '=' -f2):$(grep PORT .env | cut -d '=' -f2) --env-file .env fastapi-service

# Stop all running containers
docker-stop:
    docker stop $(docker ps -q --filter ancestor=fastapi-service) || true

# Clean up Docker resources
docker-clean: docker-stop
    docker system prune -f

# Create a new Python virtual environment
venv:
    python -m venv .venv
    . .venv/bin/activate

# Clean up Python cache files and virtual environments
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type f -name ".coverage" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    find . -type d -name "*.egg" -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".mypy_cache" -exec rm -rf {} +
    rm -rf .venv poetry.lock

vllm:
    docker run --runtime nvidia --rm --gpus all \
        -v ~/.cache/huggingface:/root/.cache/huggingface \
        -p 8000:8000 \
        --ipc=host \
        vllm/vllm-openai:latest \
        --model t-tech/T-lite-it-1.0 \
        --dtype bfloat16 \
        --max-model-len 4096 \
        --tensor-parallel-size 2 \
        --enable-prefix-caching