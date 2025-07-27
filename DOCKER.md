# Circuit Synth Docker Setup

This document explains how to use Docker with the Circuit Synth project.

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- Git (to clone the repository)

### Building and Running

#### Option 1: Using the build script (Recommended)

**Windows:**
```cmd
build-docker.bat
```

**Linux/macOS:**
```bash
./build-docker.sh
```

#### Option 2: Using Docker Compose

```bash
# Build and run the main service
docker-compose up circuit-synth

# Run in development mode with interactive shell
docker-compose run --rm circuit-synth-dev

# Run tests
docker-compose run --rm circuit-synth-test
```

#### Option 3: Manual Docker commands

```bash
# Build the image
docker build -t circuit-synth .

# Run the container
docker run --rm -v $(pwd)/src:/app/src -v $(pwd)/output:/app/output circuit-synth
```

## Build Script Options

The build scripts support several options:

```bash
# Build only (don't run)
./build-docker.sh --build-only

# Build and run tests
./build-docker.sh --run-tests

# Build and run in development mode
./build-docker.sh --dev

# Build with custom tag
./build-docker.sh --tag v1.0.0

# Show help
./build-docker.sh --help
```

## Development Workflow

### Interactive Development

For interactive development with live code changes:

```bash
# Start development container
./build-docker.sh --dev

# Or using docker-compose
docker-compose run --rm circuit-synth-dev
```

This will give you an interactive shell where you can:
- Edit code in your local `src/` directory
- Run Python scripts
- Test changes immediately
- Use the full development environment

### Running Examples

```bash
# Run a specific example
docker run --rm -it \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/examples:/app/examples \
  -v $(pwd)/output:/app/output \
  -e PYTHONPATH=/app/src \
  circuit-synth \
  python examples/example_kicad_project.py
```

### Running Tests

```bash
# Run all tests
./build-docker.sh --run-tests

# Or manually
docker run --rm \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/tests:/app/tests \
  -v $(pwd)/test_output:/app/test_output \
  -e PYTHONPATH=/app/src \
  circuit-synth \
  python -m pytest tests/ -v
```

## Volume Mounts

The Docker setup uses several volume mounts for development:

- `./src:/app/src` - Source code (live editing)
- `./examples:/app/examples` - Example projects
- `./tests:/app/tests` - Test files
- `./output:/app/output` - Generated output files
- `./cache:/app/cache` - Cache files for persistence
- `./test_output:/app/test_output` - Test output files

## Environment Variables

- `PYTHONPATH=/app/src` - Ensures Python can find the circuit_synth module
- `RUST_LOG=info` - Sets Rust logging level (use `debug` for development)
- `PYTHONUNBUFFERED=1` - Ensures Python output is not buffered
- `PYTHONDONTWRITEBYTECODE=1` - Prevents Python from writing .pyc files

## Troubleshooting

### Build Issues

1. **Rust compilation errors**: Make sure you have enough memory allocated to Docker (at least 4GB recommended)
2. **Permission errors**: The container runs as a non-root user for security
3. **Network issues**: Ensure Docker has internet access for downloading dependencies

### Runtime Issues

1. **Import errors**: Check that `PYTHONPATH` is set correctly
2. **File permission errors**: Ensure volume mounts have correct permissions
3. **Memory issues**: Increase Docker memory allocation if running large circuits

### Common Commands

```bash
# Check if container is running
docker ps

# View container logs
docker logs circuit-synth

# Enter running container
docker exec -it circuit-synth /bin/bash

# Clean up unused images
docker image prune

# Clean up everything
docker system prune -a
```

## Production Deployment

For production use, consider:

1. **Multi-stage builds** to reduce image size
2. **Security scanning** of the final image
3. **Resource limits** for CPU and memory
4. **Health checks** for container monitoring
5. **Logging configuration** for production environments

## Performance Tips

1. **Use volume mounts** instead of copying files for development
2. **Leverage Docker layer caching** by copying dependencies first
3. **Use .dockerignore** to exclude unnecessary files
4. **Consider using Docker BuildKit** for faster builds
5. **Use multi-stage builds** to separate build and runtime dependencies

## Contributing

When contributing to the Docker setup:

1. Test on both Linux and Windows
2. Ensure the build script works in CI/CD environments
3. Update this documentation for any changes
4. Consider backward compatibility
5. Test with different Docker versions 