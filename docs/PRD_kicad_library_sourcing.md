# PRD: KiCad Library Sourcing Integration

## Overview
Integrate modern KiCad library sourcing capabilities to improve component availability, reduce manual library management, and enable automated component validation in circuit-synth projects.

## Current State
- **Local Libraries**: Circuit-synth searches local KiCad installations (`/Applications/KiCad/.../symbols/`, `/Applications/KiCad/.../footprints/`)
- **Manual Process**: Users manually find symbols/footprints using `/find-symbol` and `/find-footprint` commands
- **Limited Scope**: Only searches installed KiCad libraries
- **No Validation**: No verification of component availability or manufacturing status

## Proposed Solutions

### Option 1: KiCad HTTP Library Integration
**Technology**: KiCad 9.0+ HTTP Library System
- REST API endpoints for categories and parts
- Authentication via access tokens
- Configuration through `.kicad_httplib` files
- Read-only access to external component databases

**Pros**:
- Native KiCad integration
- Standardized API format
- Future write capabilities planned

**Cons**:
- Requires KiCad 9.0+ (Feb 2025)
- Read-only currently
- Requires local symbol/footprint libraries for references

### Option 2: Third-Party API Integration
**Services**:
- **SnapEDA API**: Millions of components, IPC-7351B compliance, custom part creation
- **DigiKey API**: Supplier-verified components, BOM integration, purchasing links
- **Ultra Librarian API**: 30+ CAD formats, 2M+ components

**Pros**:
- Immediate availability
- Component sourcing integration
- Manufacturing validation

**Cons**:
- Multiple API integrations required
- Potential licensing/cost considerations
- Non-standard formats

### Option 3: Hybrid Approach
**Architecture**:
1. Local KiCad libraries (primary)
2. HTTP library system (component metadata)
3. Third-party APIs (validation/sourcing)
4. Circuit-synth orchestration layer

## Technical Implementation

### Phase 1: HTTP Library Support
- Add `.kicad_httplib` configuration generation
- Implement REST API client for component queries
- Integrate with existing symbol/footprint search commands

### Phase 2: Third-Party Integration
- SnapEDA API for component verification
- DigiKey API for availability checking
- Component caching and local storage

### Phase 3: Advanced Features
- Automated BOM validation
- Real-time component availability
- Alternative component suggestions
- Manufacturing optimization

## Implementation Status

✅ **APPROVED**: Hybrid approach (Option 3) selected  
🚧 **IN PROGRESS**: Core architecture implementation

### Architecture Implemented
- `LibraryOrchestrator`: Central coordination layer
- `BaseLibrarySource`: Abstract interface for all sources
- `LocalKiCadSource`: Local installation libraries (priority 1)
- `HTTPLibrarySource`: KiCad 9.0+ HTTP libraries (priority 2)
- `SnapEDASource`: SnapEDA API integration (priority 3)
- `DigiKeySource`: DigiKey API integration (priority 4)

### Search Strategy
1. **Parallel Search**: Query all sources simultaneously
2. **Priority Ranking**: Local → HTTP → SnapEDA → DigiKey
3. **Confidence Scoring**: 0.0-1.0 rating per result
4. **Deduplication**: Remove duplicate symbol/footprint combinations
5. **Fallback Logic**: Try next source if primary fails

## Implementation Decisions

### **API Configuration** ✅
- API credentials are user responsibility
- Agent will provide setup assistance
- No built-in credential management

### **Search Behavior** ✅ 
- Reference-based or connection-based search
- Backup to local KiCad symbol search
- Show source information in results

### **Component Validation** ✅
- No automatic validation during circuit generation
- No stock/price warnings
- No alternative suggestions (keep simple)

### **Caching and Performance** ✅
- Cache API results to `.cache/` folder
- Standard cache TTL (1 hour default)
- No pre-downloading of libraries

### **Integration Points** ✅
- Integrate as backup to existing `/find-symbol` and `/find-footprint`
- No BOM export integration (future feature)
- No manufacturing optimization (out of scope)

## Final Architecture

### Core Components
1. **LibraryOrchestrator**: Coordinates search across sources
2. **Local KiCad Fallback**: Try APIs when local search fails
3. **Cache System**: Store results in `.cache/kicad-library-sourcing/`
4. **Agent Setup**: Help users configure API credentials

### Search Flow
```
User: /find-symbol STM32F4
  ↓
1. Search local KiCad libraries first
  ↓ (if no results)
2. Search HTTP libraries + SnapEDA + DigiKey in parallel
  ↓
3. Cache results to .cache/
  ↓
4. Return combined results with source tags
```

### Command Integration
- Extend existing `/find-symbol` and `/find-footprint` commands
- Add fallback search when local results insufficient
- Display source information: `[Local]`, `[SnapEDA]`, `[DigiKey]`

## Success Metrics
- Reduced time to find appropriate components
- Increased component availability accuracy
- Improved manufacturing success rate
- Enhanced automated component validation

## Dependencies
- KiCad 9.0+ for HTTP library system
- API access to third-party services
- Local storage for component caching
- Network connectivity for real-time validation