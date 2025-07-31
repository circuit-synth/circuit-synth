# Docker Quick Reference - Circuit-Synth

## Current Status
- ✅ **Basic Container**: Built and working (`circuit-synth:simple`)
- 🚧 **KiCad Integration**: Ready to test with library mounting
- 📋 **Next Step**: Download KiCad libraries and test full functionality

## Ready-to-Execute Commands

### 1. Setup KiCad Libraries (First Time)
```bash
# Navigate to project directory
cd /Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth

# Create directories and download KiCad libraries
mkdir -p kicad-libraries output
git clone --depth=1 https://gitlab.com/kicad/libraries/kicad-symbols.git kicad-libraries/symbols
git clone --depth=1 https://gitlab.com/kicad/libraries/kicad-footprints.git kicad-libraries/footprints
```

### 2. Test Full Circuit-Synth with KiCad
```bash
# Run example with KiCad libraries mounted
docker run --rm \
  -v "$(pwd)/examples":/app/examples \
  -v "$(pwd)/output":/app/output \
  -v "$(pwd)/kicad-libraries/symbols":/usr/share/kicad/symbols:ro \
  -v "$(pwd)/kicad-libraries/footprints":/usr/share/kicad/footprints:ro \
  -e KICAD_SYMBOL_DIR=/usr/share/kicad/symbols \
  -e KICAD_FOOTPRINT_DIR=/usr/share/kicad/footprints \
  circuit-synth:simple python examples/example_kicad_project.py
```

### 3. Verify Results
```bash
# Check generated files
ls -la output/
# Should see .kicad_pro, .kicad_sch, and related files
```

## Alternative Testing Methods

### Mock Library Test (Quick)
```bash
# Test with mock libraries to verify Docker setup
docker run --rm \
  -v "$(pwd)/examples":/app/examples \
  -v "$(pwd)/output":/app/output \
  circuit-synth:simple python examples/example_kicad_project.py
```

### Docker Compose Method
```bash
# Use pre-configured Docker Compose setup
docker-compose -f docker/docker-compose.kicad.yml up
```

### Build KiCad-Enabled Container
```bash
# Build container with integrated KiCad
docker build -t circuit-synth:kicad -f docker/Dockerfile.kicad-integrated .
```

## Container Management

### Basic Operations
```bash
# Build basic container
docker build -t circuit-synth:simple -f Dockerfile .

# List images
docker images | grep circuit-synth

# Remove container
docker rmi circuit-synth:simple

# Interactive shell
docker run --rm -it circuit-synth:simple bash
```

### Debugging
```bash
# Run with interactive shell for debugging
docker run --rm -it \
  -v "$(pwd)/examples":/app/examples \
  -v "$(pwd)/output":/app/output \
  circuit-synth:simple bash

# Inside container, test components
python -c "import circuit_synth; print('Circuit-Synth loaded')"
python examples/example_kicad_project.py
```

## Available Docker Configurations

| File | Purpose | Status |
|------|---------|--------|
| `Dockerfile` | Basic Circuit-Synth | ✅ Working |
| `docker/Dockerfile.kicad-integrated` | Multi-stage with KiCad | 📋 Ready to test |
| `docker/Dockerfile.kicad-emulated` | Cross-platform | 📋 Available |
| `docker/Dockerfile.kicad-production` | Production-ready | 📋 Available |

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `KICAD_SYMBOL_DIR` | Symbol library path | `/usr/share/kicad/symbols` |
| `KICAD_FOOTPRINT_DIR` | Footprint library path | `/usr/share/kicad/footprints` |

## Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./examples` | `/app/examples` | Python example scripts |
| `./output` | `/app/output` | Generated KiCad files |
| `./kicad-libraries/symbols` | `/usr/share/kicad/symbols` | KiCad symbol libraries |
| `./kicad-libraries/footprints` | `/usr/share/kicad/footprints` | KiCad footprint libraries |

## Expected Output Structure
After successful run, `output/` should contain:
```
output/
├── example_kicad_project.kicad_pro    # Project file
├── example_kicad_project.kicad_sch    # Main schematic
├── *.kicad_sch                       # Sub-schematics
└── example_kicad_project.kicad_pcb    # PCB layout (if generated)
```

## Troubleshooting

### Common Issues
1. **Library not found**: Ensure KiCad libraries are downloaded and mounted correctly
2. **Permission errors**: Check volume mount permissions (use `:ro` for read-only)
3. **Container build fails**: Verify Docker daemon is running and has sufficient resources

### Debug Commands
```bash
# Check if libraries are accessible in container
docker run --rm -it \
  -v "$(pwd)/kicad-libraries/symbols":/usr/share/kicad/symbols:ro \
  circuit-synth:simple \
  ls -la /usr/share/kicad/symbols

# Test Python imports
docker run --rm circuit-synth:simple python -c "import circuit_synth; print('Success')"
```

## Next Development Steps
1. ✅ Basic container working
2. 📋 **IMMEDIATE**: Download KiCad libraries and test full functionality
3. 📋 Test ARM64 compatibility with sophisticated Docker configs
4. 📋 Integrate into CI/CD pipeline
5. 📋 Production deployment configuration