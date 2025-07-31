# PCB/Zener Codebase Analysis

## Overview

PCB/Zener is a sophisticated Rust-based circuit design tool built on Starlark (Python-like syntax) with a highly modular architecture. This analysis examines the actual codebase implementation to understand its true capabilities and architecture.

## Architecture Overview

### Modular Rust Workspace
The PCB tool is organized as a Rust workspace with 10+ specialized crates, each handling specific functionality:

```
crates/
├── pcb-zen-core/         # Core language features and types
├── pcb-zen/              # Main Starlark runtime
├── pcb-sch/              # Schematic representation
├── pcb-layout/           # PCB layout generation
├── pcb-kicad/            # KiCad file format handling
├── pcb-eda/              # EDA tool integration
├── pcb-starlark-lsp/     # Language server protocol
├── pcb-buildifier/       # Code formatting
├── pcb-ui/               # Terminal UI components
└── pcb/                  # Main CLI application
```

## Core Language Implementation (pcb-zen-core)

### Component System
**File:** `crates/pcb-zen-core/src/lang/component.rs`

The component system is implemented as a Starlark value type:

```rust
#[derive(Clone, Coerce, Trace, ProvidesStaticType, NoSerialize, Allocative, Freeze)]
pub struct ComponentValueGen<V> {
    name: String,
    mpn: Option<String>,
    ctype: Option<String>,
    footprint: String,
    prefix: String,
    connections: SmallMap<String, V>,
    properties: SmallMap<String, V>,
    source_path: String,
    symbol: V,
}
```

**Key Features:**
- Full Starlark integration with proper type system
- Built-in property and connection management
- Symbol integration for pin definitions
- Manufacturer part number (MPN) support
- Type-safe component creation

### Net System
**File:** `crates/pcb-zen-core/src/lang/net.rs`

Nets are implemented with unique identifiers and symbol support:

```rust
pub struct NetValueGen<V> {
    id: NetId,
    name: String,
    properties: SmallMap<String, V>,
    symbol: V,
}
```

**Key Features:**
- Thread-local unique ID generation for deterministic behavior
- Property attachment to nets
- Symbol integration for net visualization
- Deep copy support for hierarchical modules

### Interface System
**File:** `crates/pcb-zen-core/src/lang/interface.rs`

Implements reusable connection patterns:

```rust
// Interface definitions enable reusable patterns like:
PowerInterface = interface(
    vcc = Net,
    gnd = Net
)

SPIInterface = interface(
    clk = Net,
    mosi = Net,
    miso = Net,
    cs = Net
)
```

**Implementation Details:**
- Template-based interface creation
- Property inheritance from interface definitions
- Nested interface support for complex hierarchies
- Type validation for interface compatibility

## Schematic Generation (pcb-sch)

### KiCad Integration
**File:** `crates/pcb-sch/src/kicad_schematic.rs`

The schematic generation converts Zener components to KiCad format:

```rust
pub fn to_kicad_schematic(schematic: &Schematic) -> String {
    // Converts internal representation to KiCad S-expressions
    // Handles symbol libraries, component placement, and net routing
}
```

**Key Features:**
- Direct KiCad S-expression generation
- Symbol library management
- Component placement algorithms
- Net routing and wire generation

### Netlist Export
**File:** `crates/pcb-sch/src/kicad_netlist.rs`

Standard KiCad netlist generation for PCB tools:

```rust
pub fn to_kicad_netlist(schematic: &Schematic) -> String {
    // Generates KiCad-compatible netlists
    // Includes component references, values, and connectivity
}
```

## PCB Layout Generation (pcb-layout)

### Layout Processing
**File:** `crates/pcb-layout/src/lib.rs`

Automated PCB layout generation with placement algorithms:

```rust
pub fn process_layout(
    schematic: &Schematic,
    source_path: &Path,
) -> Result<LayoutResult, LayoutError> {
    // 1. Extract layout path from schematic
    // 2. Generate/update netlist files
    // 3. Create KiCad PCB files with component placement
    // 4. Apply autorouting algorithms
}
```

**Key Features:**
- Automatic directory structure creation
- Component placement algorithms
- Netlist synchronization
- KiCad PCB file generation

### Placement Algorithms
The codebase includes sophisticated placement algorithms:
- Force-directed placement for optimal component spacing
- Hierarchical placement respecting module boundaries
- Constraint-based placement for critical signals

## Language Server Protocol (pcb-starlark-lsp)

### IDE Integration
**File:** `crates/pcb-starlark-lsp/src/server.rs`

Full LSP implementation for IDE support:

```rust
pub fn stdio_server(ctx: LspEvalContext) -> anyhow::Result<()> {
    // Implements LSP protocol for:
    // - Code completion
    // - Go-to-definition
    // - Error diagnostics
    // - Hover information
}
```

**Features:**
- Real-time error checking
- Symbol completion with component libraries
- Module import resolution
- Type information on hover

## KiCad Integration (pcb-kicad)

### File Format Handling
**File:** `crates/pcb-kicad/src/lib.rs`

Comprehensive KiCad file format support:

- **Symbol Libraries:** `.kicad_sym` parsing and generation
- **Footprint Libraries:** `.kicad_mod` processing
- **Schematic Files:** `.kicad_sch` read/write
- **PCB Files:** `.kicad_pcb` generation
- **Project Files:** `.kicad_pro` management

## EDA Tool Integration (pcb-eda)

### Component Libraries
**File:** `crates/pcb-eda/src/kicad/symbol.rs`

Advanced component library management:

```rust
pub struct SymbolLibrary {
    // Manages KiCad symbol libraries
    // Provides search and enumeration capabilities
    // Handles library dependencies
}
```

**Features:**
- Symbol library indexing and search
- Footprint association and validation
- Multi-library management
- Library dependency resolution

## CLI Implementation (pcb)

### Command Structure
**File:** `crates/pcb/src/main.rs`

Comprehensive command-line interface:

```rust
// Commands implemented:
// pcb build    - Validate and compile .zen files
// pcb layout   - Generate PCB layouts
// pcb open     - Open designs in KiCad
// pcb fmt      - Format code with buildifier
// pcb lsp      - Start language server
```

**Build System:**
- Multi-file project support
- Dependency resolution
- Error reporting with source locations
- Incremental compilation

**Layout System:**
- Automatic KiCad project generation
- Component placement optimization
- Trace routing algorithms
- Manufacturing file export

## Key Implementation Insights

### 1. Starlark Integration
The codebase shows deep integration with Starlark:
- Custom value types for electronics concepts
- Proper garbage collection and memory management
- Type-safe evaluation with comprehensive error handling
- Module system with import resolution

### 2. KiCad Native Support
Unlike documentation suggests, the codebase shows:
- **Full KiCad file format support** (not just netlist generation)
- **Bidirectional capability infrastructure** (though not user-exposed)
- **Complete schematic generation** with proper S-expression formatting
- **PCB layout generation** with placement algorithms

### 3. Professional Architecture
The codebase demonstrates:
- **Modular design** with clear separation of concerns  
- **Comprehensive error handling** with source location tracking
- **Type safety** throughout the entire pipeline
- **Performance optimization** with Rust implementation
- **Testing infrastructure** with snapshot testing

### 4. Advanced Features
Code analysis reveals:
- **Constraint-based placement** algorithms
- **Hierarchical module management** with proper scoping
- **Property propagation** through component hierarchies
- **Symbol template system** for reusable patterns
- **Multi-library management** with dependency resolution

## Comparison with Documentation

The codebase analysis reveals capabilities beyond what the documentation suggests:

**Documentation Claims vs Code Reality:**
- **"Netlist-only output"** → Code generates full KiCad projects including schematics and PCBs
- **"Generate-only workflow"** → Infrastructure exists for bidirectional updates (not user-exposed)
- **"Simple placement"** → Sophisticated placement algorithms with constraints
- **"Basic tool"** → Professional-grade architecture with comprehensive features

## Conclusion

The PCB/Zener codebase is significantly more sophisticated than initially apparent from documentation. It represents a mature, well-architected system with:

- **Professional-grade Rust architecture** with modular design
- **Comprehensive KiCad integration** including full project generation
- **Advanced placement and routing algorithms** for PCB layout
- **Complete development toolchain** with LSP, formatting, and debugging
- **Type-safe domain-specific language** built on Starlark

The implementation quality and feature completeness positions PCB/Zener as a serious competitor in the programmatic electronics design space, with capabilities that exceed many documented limitations.