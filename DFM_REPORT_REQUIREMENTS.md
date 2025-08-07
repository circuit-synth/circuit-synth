# DFM Report Requirements - Real Data Only

## Critical Requirements

### 1. NO ESTIMATES OR PLACEHOLDERS
- **All component prices MUST come from real supplier APIs** (DigiKey, Mouser, etc.)
- **Never estimate or assume costs** - if data is unavailable, mark as "Data Not Available"
- **No AI-generated content** - only factual, verifiable information
- **Every price must cite its source** (supplier name, part number, date retrieved)

### 2. Data Sources

#### Component Pricing (Required)
- **Primary Source**: DigiKey API
- **Alternative Sources**: Mouser API, Octopart API
- **Required Fields**:
  - Unit price at Qty 1
  - Price breaks (10, 25, 100, 250, 500, 1000, 2500, 5000, 10000)
  - Stock availability
  - Lead time
  - Minimum order quantity
  - Manufacturer name
  - Manufacturer part number
  - Distributor part number

#### What NOT to Include (No Real Data Available)
- ❌ PCB fabrication costs (unless using real PCB manufacturer API)
- ❌ Assembly costs (unless using real assembly house quotes)
- ❌ Shipping costs (unless calculated from real carriers)
- ❌ Taxes and duties (unless calculated from real rates)
- ❌ NRE costs (unless provided by manufacturer)

### 3. Report Structure

#### Executive Summary
```
BILL OF MATERIALS ANALYSIS - REAL SUPPLIER DATA
================================================
Data Source: DigiKey API
Report Date: 2025-01-28 14:30:00 UTC
Currency: USD

COVERAGE:
- Total Components: 49
- Components with Pricing: 42 (85.7%)
- Missing Pricing: 7 components [list them]

BOM COST (Components Only):
Qty     BOM Cost    Per Unit    Coverage
1       $45.23      $45.23      85.7%
100     $38.45      $38.45      85.7%
1000    $32.10      $32.10      85.7%

NOTE: Prices shown are for components only.
      PCB and assembly costs are NOT included.
```

#### Component Details Table
```
Ref  Part Number         DigiKey P/N        Qty1    Qty100  Qty1000  Stock
U1   ESP32-C6-MINI-1    1234-5678-ND       $4.50   $4.25   $3.95    2,450
C1   CL10A106KP8NNNC    587-1234-1-ND      $0.08   $0.05   $0.03    145,230
R1   RC0603FR-0710KL    311-10.0KHRCT-ND   $0.10   $0.01   $0.003   589,455
[NOT FOUND] U5 - TPS12345 - No DigiKey match
```

### 4. Implementation Requirements

#### Python Code Structure
```python
class RealDataDFMAnalyzer:
    def analyze_bom_pricing(self, components):
        # ONLY use real API calls
        for component in components:
            pricing = self.get_digikey_pricing(component)
            if not pricing:
                # Mark as "Not Found" - never estimate
                component.status = "No Pricing Available"
        
    def generate_report(self):
        # Clearly indicate data sources
        report.add_header("Data Source: DigiKey API")
        report.add_header(f"Prices Retrieved: {datetime.now()}")
        
        # Show coverage percentage
        coverage = priced_components / total_components * 100
        report.add_metric(f"Price Coverage: {coverage:.1f}%")
        
        # List missing components
        if missing_components:
            report.add_section("Components Without Pricing", missing_components)
```

### 5. API Configuration

#### DigiKey Setup
```bash
# Configure DigiKey API credentials
python -m circuit_synth.manufacturing.digikey.config_manager

# Required environment variables
export DIGIKEY_CLIENT_ID="your_client_id"
export DIGIKEY_CLIENT_SECRET="your_client_secret"
export DIGIKEY_SANDBOX="false"  # Use production API
```

### 6. Report Validation Checklist

Before releasing any DFM report:
- [ ] All prices come from verified API responses
- [ ] Each price has a timestamp
- [ ] Coverage percentage is clearly shown
- [ ] Missing components are explicitly listed
- [ ] Report states "Components Only - No PCB/Assembly Costs"
- [ ] Data source (DigiKey, Mouser, etc.) is prominently displayed
- [ ] No placeholder values anywhere in the report

### 7. Example Output

```
ESP32 Development Board - BOM Analysis
=======================================
Report Generated: 2025-01-28 14:45:23 UTC
Data Source: DigiKey Production API
Total Components: 49
Priced Components: 42 (85.7%)

MISSING PRICING DATA:
- U5: Custom ASIC (no distributor stock)
- J3: Proprietary connector
- Y1: 26MHz crystal (specification unclear)

BOM PRICING BY QUANTITY (USD):
Quantity    BOM Cost    Unit Cost   Savings
1           $45.23      $45.23      -
10          $42.15      $42.15      6.8%
100         $38.45      $38.45      15.0%
1000        $32.10      $32.10      29.0%

TOP 5 COST DRIVERS:
1. U1 ESP32-C6-MINI-1: $4.50 (9.9% of BOM)
2. U3 CP2102N: $2.85 (6.3% of BOM)
3. J1 USB-C Connector: $1.25 (2.8% of BOM)
4. U2 AMS1117-3.3: $0.45 (1.0% of BOM)
5. U4 ESD Protection: $0.38 (0.8% of BOM)

IMPORTANT NOTICE:
This analysis includes component costs only.
PCB fabrication and assembly costs are not included.
All prices from DigiKey as of 2025-01-28.
Prices subject to change. Verify before ordering.
```

## Summary

The DFM system has been updated to:
1. **Use only real supplier data** - no estimates or placeholders
2. **Clearly indicate data sources** - DigiKey API with timestamps
3. **Show coverage percentage** - what % of BOM has real pricing
4. **List missing components** - transparency about what couldn't be priced
5. **Exclude uncertain costs** - no PCB or assembly cost guesses

This ensures the reports contain only factual, verifiable information that can be trusted for production planning.