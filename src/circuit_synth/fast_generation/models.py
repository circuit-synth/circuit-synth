"""
AI Model integrations for fast circuit generation
"""

import os
from typing import Dict, List, Optional, Any
import asyncio
import logging
from dataclasses import dataclass

try:
    import openai
except ImportError:
    openai = None

try:
    from google.adk.agents import Agent
    from google.adk.tools import google_search
except ImportError:
    Agent = None
    google_search = None

from .pin_finder import pin_finder, get_ai_pin_context, adk_pin_finder_tool
from .adk_tools import create_adk_tools

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    """Standard response format from AI models"""
    content: str
    model: str
    tokens_used: int
    latency_ms: float
    success: bool
    error: Optional[str] = None


class OpenRouterModel:
    """OpenRouter API client for Gemini-2.5-Flash"""
    
    def __init__(self, api_key: str = None, model: str = "google/gemini-2.5-flash"):
        if not api_key:
            api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            raise ValueError("OpenRouter API key required. Set OPENROUTER_API_KEY env var.")
        
        if not openai:
            raise ImportError("OpenAI library required: pip install openai")
        
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = model
        
    async def generate_circuit(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None,
        max_tokens: int = 4000
    ) -> ModelResponse:
        """Generate circuit code using OpenRouter Gemini-2.5-Flash"""
        import time
        start_time = time.time()
        
        try:
            # Extract components from context and get pin information
            components = context.get("components", []) if context else []
            pin_context = ""
            if components:
                pin_context = self._get_pin_information(components)
            
            # Build system message with context and pin information
            full_context = dict(context or {})
            if pin_context:
                full_context["pin_information"] = pin_context
            
            system_msg = self._build_system_message(full_context)
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1  # Low temperature for consistent code generation
            )
            
            latency = (time.time() - start_time) * 1000
            
            return ModelResponse(
                content=response.choices[0].message.content,
                model=self.model,
                tokens_used=response.usage.total_tokens,
                latency_ms=latency,
                success=True
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error(f"OpenRouter generation failed: {e}")
            
            return ModelResponse(
                content="",
                model=self.model,
                tokens_used=0,
                latency_ms=latency,
                success=False,
                error=str(e)
            )
    
    def _get_pin_information(self, components: List[str]) -> str:
        """Get pin information for components using pin finder"""
        logger.info(f"🔍 Finding pin information for {len(components)} components")
        
        pin_info_parts = []
        for symbol in components:
            try:
                pin_info = pin_finder.get_pin_info_for_ai(symbol)
                pin_info_parts.append(f"\n{pin_info}")
                logger.debug(f"✅ Found pins for {symbol}")
            except Exception as e:
                error_msg = f"❌ Could not find pins for {symbol}: {e}"
                pin_info_parts.append(error_msg)
                logger.warning(error_msg)
        
        return "\n".join(pin_info_parts)
    
    def _build_system_message(self, context: Dict[str, Any]) -> str:
        """Build system message with circuit generation context"""
        base_msg = """You are a professional circuit design engineer specializing in circuit-synth projects.

CRITICAL REQUIREMENTS:
1. Generate ONLY Python code using circuit-synth syntax - NO markdown fences
2. Use EXACT working KiCad symbols and footprints from verified list
3. Use ONLY the EXACT pin names provided in the PIN INFORMATION section below
4. Follow the EXACT syntax patterns from reference circuits
5. Include proper @circuit decorator and function structure
6. Use correct pin connection syntax: component["pin_name"] += net

⚠️  NEVER GUESS PIN NAMES - Use only pins listed in PIN INFORMATION section below!

📚 REFERENCE CIRCUITS: Study these working examples for proper syntax:
- ESP32 Basic: /src/circuit_synth/fast_generation/reference_circuits/esp32_basic.py
- ESP32 Sensor: /src/circuit_synth/fast_generation/reference_circuits/esp32_sensor.py  
- STM32 Basic: /src/circuit_synth/fast_generation/reference_circuits/stm32_basic.py
- Motor Driver: /src/circuit_synth/fast_generation/reference_circuits/motor_stepper.py
- LED Driver: /src/circuit_synth/fast_generation/reference_circuits/led_neopixel.py
- USB Power: /src/circuit_synth/fast_generation/reference_circuits/usb_power.py

CORRECT CIRCUIT-SYNTH SYNTAX:
```python
from circuit_synth import *

@circuit(name="CircuitName")  
def my_circuit():
    # Create nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Create components with EXACT symbols
    mcu = Component(
        symbol="MCU_Espressif:ESP32-S3",
        ref="U",
        footprint="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm"
    )
    
    # Connect pins using EXACT pin names
    mcu["VDD"] += vcc_3v3
    mcu["VSS"] += gnd
    
if __name__ == "__main__":
    circuit_obj = my_circuit()
    circuit_obj.generate_kicad_project(
        project_name="MyProject",
        placement_algorithm="hierarchical", 
        generate_pcb=True
    )
    print("✅ KiCad project generated!")
```

VERIFIED WORKING COMPONENTS:
- ESP32-S3: symbol="MCU_Espressif:ESP32-S3", footprint="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm"
- ESP32-C6: symbol="RF_Module:ESP32-C6-MINI-1", footprint="RF_Module:ESP32-C6-MINI-1"
- STM32F4: symbol="MCU_ST_STM32F4:STM32F411CEUx", footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
- Resistor: symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric"
- Capacitor: symbol="Device:C", footprint="Capacitor_SMD:C_0603_1608Metric"
- LED: symbol="Device:LED", footprint="LED_SMD:LED_0603_1608Metric"

PIN CONNECTION RULES:
- Power pins: mcu["VDD"] += vcc_3v3, mcu["VSS"] += gnd
- GPIO pins: mcu["IO8"] += signal_net
- Passive components: resistor[1] += net1, resistor[2] += net2
- NO .pin() method - use direct bracket notation

GENERATE COMPLETE WORKING CODE WITH:
- @circuit decorator
- Proper component definitions  
- Correct pin connections
- KiCad project generation in __main__
"""
        
        # Add specific context
        if "pattern_type" in context:
            base_msg += f"\nTARGET PATTERN: {context['pattern_type']}"
        
        if "components" in context:
            base_msg += f"\nREQUIRED COMPONENTS: {', '.join(context['components'])}"
        
        if "kicad_components" in context:
            base_msg += f"\nVERIFIED KICAD SYMBOLS: {context['kicad_components']}"
        
        # Add exact pin information if available - make it very prominent
        if "pin_information" in context and context["pin_information"]:
            base_msg += f"\n\n{'='*80}"
            base_msg += f"\n🔥 MANDATORY PIN INFORMATION - USE THESE EXACT NAMES ONLY!"
            base_msg += f"\n{'='*80}"
            base_msg += f"\n{context['pin_information']}"
            base_msg += f"\n{'='*80}"
            base_msg += f"\n⚠️  CRITICAL: Use ONLY the pin names listed above!"
            base_msg += f"\n⚠️  Example: mpu6050['VDD'] += power_net (NOT mpu6050['VCC'])"
            base_msg += f"\n{'='*80}"
            
        return base_msg


class GoogleADKModel:
    """Google ADK Agent for circuit generation orchestration"""
    
    def __init__(self, project_id: str = None):
        if not Agent:
            raise ImportError("Google ADK required: pip install google-adk")
        
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.agents = {}
        self._setup_agents()
    
    def _setup_agents(self):
        """Setup specialized circuit generation agents"""
        
        # Create all available ADK tools
        tools = create_adk_tools()
        logger.info(f"Created {len(tools)} ADK tools for circuit design")
        
        # Main circuit generator agent
        self.agents["generator"] = Agent(
            name="circuit_generator",
            model="gemini-2.5-flash",
            instruction="""You are a circuit design specialist. Generate production-ready 
            KiCad circuit-synth code following electrical engineering best practices.
            
            CRITICAL: Always use these tools before generating circuits:
            1. find_symbol_tool_function() - Find correct KiCad symbols
            2. find_footprint_tool_function() - Find matching footprints  
            3. find_pins_tool_function() - Get exact pin names
            
            This ensures you use verified components with correct pin names.""",
            description="Primary circuit code generation",
            tools=tools
        )
        
        # Component validator agent  
        self.agents["validator"] = Agent(
            name="component_validator", 
            model="gemini-2.5-flash",
            instruction="""Validate that all components exist in KiCad libraries and 
            verify electrical connections are correct. Use find_pins_tool_function to verify pin names.""",
            description="Component and connection validation",
            tools=tools
        )
        
        # Pattern specialist agent
        self.agents["patterns"] = Agent(
            name="pattern_specialist",
            model="gemini-2.5-flash", 
            instruction="""Specialize in common circuit patterns: MCU boards, sensor 
            integration, motor control, power management.""",
            description="Circuit pattern expertise",
            tools=[]
        )
    
    async def generate_with_agents(
        self,
        pattern_type: str,
        requirements: Dict[str, Any]
    ) -> ModelResponse:
        """Generate circuit using coordinated agents"""
        import time
        start_time = time.time()
        
        try:
            # Use pattern specialist to determine approach
            pattern_agent = self.agents["patterns"]
            approach = await self._query_agent(
                pattern_agent,
                f"Analyze requirements for {pattern_type}: {requirements}"
            )
            
            # Use main generator to create circuit
            generator_agent = self.agents["generator"]
            circuit_code = await self._query_agent(
                generator_agent,
                f"Generate circuit-synth code for: {approach}"
            )
            
            # Use validator to check result
            validator_agent = self.agents["validator"]
            validation = await self._query_agent(
                validator_agent,
                f"Validate this circuit code: {circuit_code}"
            )
            
            latency = (time.time() - start_time) * 1000
            
            return ModelResponse(
                content=circuit_code,
                model="gemini-2.5-flash-adk",
                tokens_used=0,  # TODO: Track token usage
                latency_ms=latency,
                success=True
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error(f"Google ADK generation failed: {e}")
            
            return ModelResponse(
                content="",
                model="gemini-2.5-flash-adk",
                tokens_used=0,
                latency_ms=latency,
                success=False,
                error=str(e)
            )
    
    async def _query_agent(self, agent: Any, prompt: str) -> str:
        """Query an ADK agent (placeholder - implement based on actual ADK API)"""
        # This is a placeholder - actual implementation depends on ADK API
        # For demo, we'll simulate with a simple response
        await asyncio.sleep(0.1)  # Simulate processing
        return f"ADK Response to: {prompt[:100]}..."