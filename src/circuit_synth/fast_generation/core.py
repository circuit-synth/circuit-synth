"""
Fast Circuit Generation Core

Main orchestration for high-speed circuit generation using templates and AI models.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .models import OpenRouterModel, GoogleADKModel, ModelResponse
from .patterns import CircuitPatterns, PatternType, PatternTemplate
from .project_templates import ProjectTemplateGenerator

logger = logging.getLogger(__name__)


class FastCircuitGenerator:
    """High-speed circuit generator using patterns and AI models"""
    
    def __init__(
        self,
        openrouter_key: str = None,
        google_project: str = None,
        default_model: str = "openrouter"
    ):
        """Initialize fast circuit generator"""
        self.openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")
        self.google_project = google_project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.default_model = default_model
        
        # Initialize AI models
        self.models = {}
        self._setup_models()
        
        # Load patterns
        self.patterns = CircuitPatterns()
        
        # Project template generator
        self.project_generator = ProjectTemplateGenerator()
        
        # Performance tracking
        self.generation_stats = {
            "total_generated": 0,
            "avg_latency_ms": 0,
            "success_rate": 0.0,
            "pattern_usage": {}
        }
    
    def _setup_models(self):
        """Setup AI model integrations"""
        try:
            if self.openrouter_key:
                self.models["openrouter"] = OpenRouterModel(
                    api_key=self.openrouter_key,
                    model="google/gemini-2.5-flash"
                )
                logger.info("✅ OpenRouter model initialized")
            else:
                logger.warning("⚠️ OpenRouter API key not provided")
                
        except Exception as e:
            logger.error(f"❌ Failed to setup OpenRouter: {e}")
        
        try:
            if self.google_project:
                self.models["google_adk"] = GoogleADKModel(
                    project_id=self.google_project
                )
                logger.info("✅ Google ADK model initialized") 
            else:
                logger.info("ℹ️ Google ADK not configured (optional)")
                
        except Exception as e:
            logger.error(f"❌ Failed to setup Google ADK: {e}")
    
    async def generate_circuit(
        self,
        pattern_type: Union[str, PatternType],
        requirements: Dict[str, Any] = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Generate circuit code for a specific pattern
        
        Args:
            pattern_type: Type of circuit pattern to generate
            requirements: Additional requirements and customizations
            model: AI model to use ("openrouter" or "google_adk")
            
        Returns:
            Dict with generated code, metadata, and performance info
        """
        start_time = datetime.now()
        
        try:
            # Parse pattern type
            if isinstance(pattern_type, str):
                pattern_type = PatternType(pattern_type)
            
            # Get pattern template
            template = self.patterns.get_pattern(pattern_type)
            if not template:
                raise ValueError(f"Pattern {pattern_type} not found")
            
            # Choose model
            model_name = model or self.default_model
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not available")
            
            # Build generation context
            context = self._build_context(template, requirements or {})
            
            # Generate circuit using selected model
            ai_model = self.models[model_name]
            if model_name == "openrouter":
                response = await self._generate_with_openrouter(
                    ai_model, template, context
                )
            elif model_name == "google_adk":
                response = await self._generate_with_google_adk(
                    ai_model, template, context
                )
            else:
                raise ValueError(f"Unknown model: {model_name}")
            
            # Process and validate result
            result = await self._process_generation_result(
                response, template, context
            )
            
            # Update statistics
            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000
            self._update_stats(pattern_type, latency_ms, response.success)
            
            return {
                "success": response.success,
                "circuit_code": result["circuit_code"],
                "kicad_project": result.get("kicad_project"),
                "pattern": template.name,
                "model_used": model_name,
                "latency_ms": latency_ms,
                "tokens_used": response.tokens_used,
                "validation_results": result.get("validation", {}),
                "error": response.error
            }
            
        except Exception as e:
            logger.error(f"Circuit generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "circuit_code": None,
                "pattern": pattern_type.value if isinstance(pattern_type, PatternType) else str(pattern_type),
                "latency_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
    
    def _build_context(
        self, 
        template: PatternTemplate, 
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context for AI generation"""
        
        # Extract verified KiCad components from template
        kicad_components = {}
        for comp in template.components:
            kicad_components[comp.ref_prefix] = {
                "symbol": comp.symbol,
                "footprint": comp.footprint,
                "description": comp.description
            }
        
        context = {
            "pattern_type": template.name,
            "description": template.description,
            "components": [comp.symbol for comp in template.components],
            "kicad_components": kicad_components,
            "power_rails": template.power_rails,
            "design_notes": template.design_notes,
            "estimated_complexity": template.estimated_complexity,
            "requirements": requirements
        }
        
        # Add component connection hints
        if template.connections:
            context["connection_hints"] = template.connections
            
        return context
    
    async def _generate_with_openrouter(
        self,
        model: OpenRouterModel,
        template: PatternTemplate, 
        context: Dict[str, Any]
    ) -> ModelResponse:
        """Generate circuit using OpenRouter Gemini"""
        
        prompt = self._build_generation_prompt(template, context)
        return await model.generate_circuit(prompt, context, max_tokens=4000)
    
    async def _generate_with_google_adk(
        self,
        model: GoogleADKModel,
        template: PatternTemplate,
        context: Dict[str, Any]
    ) -> ModelResponse:
        """Generate circuit using Google ADK agents"""
        
        requirements = {
            "pattern": template.name,
            "components": context["components"],
            "power_rails": context["power_rails"],
            "custom_requirements": context.get("requirements", {})
        }
        
        return await model.generate_with_agents(
            template.name, 
            requirements
        )
    
    def _build_generation_prompt(
        self,
        template: PatternTemplate,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for circuit generation"""
        
        prompt = f"""Generate a complete circuit-synth Python project for: {template.name}

REQUIREMENTS:
{template.description}

VERIFIED COMPONENTS TO USE:
"""
        
        for comp in template.components:
            prompt += f"- {comp.symbol} ({comp.footprint}) - {comp.description}\n"
        
        prompt += f"""
POWER RAILS REQUIRED: {', '.join(template.power_rails)}

DESIGN NOTES:
"""
        for note in template.design_notes:
            prompt += f"- {note}\n"
        
        if context.get("connection_hints"):
            prompt += "\nCONNECTION HINTS:\n"
            for conn in context["connection_hints"]:
                prompt += f"- Connect {conn.get('from', 'N/A')} to {conn.get('to', 'N/A')}\n"
        
        prompt += """
MANDATORY WORKFLOW:
1. Use ONLY the verified components listed above
2. For each component, use the /find-pins command to get exact pin names
3. Generate syntactically correct circuit-synth Python code
4. Include proper power distribution and decoupling
5. Add debug/programming interfaces where applicable
6. Follow the design notes carefully

Generate complete circuit-synth code with:
- All necessary imports
- Component definitions with exact symbols/footprints
- Proper net connections using verified pin names
- Power rail distribution
- Export functions for KiCad generation

IMPORTANT: Only use the exact KiCad symbols and footprints specified above.
"""
        
        # Add custom requirements if provided
        custom_reqs = context.get("requirements", {})
        if custom_reqs:
            prompt += f"\nCUSTOM REQUIREMENTS:\n{custom_reqs}\n"
        
        return prompt
    
    async def _process_generation_result(
        self,
        response: ModelResponse,
        template: PatternTemplate,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and validate generation result"""
        
        result = {
            "circuit_code": response.content,
            "validation": {
                "syntax_valid": False,
                "components_verified": False,
                "connections_valid": False
            }
        }
        
        if response.success and response.content:
            # Basic syntax validation
            try:
                # Simple check for Python syntax
                compile(response.content, '<string>', 'exec')
                result["validation"]["syntax_valid"] = True
            except SyntaxError:
                logger.warning("Generated code has syntax errors")
            
            # Check for required components
            component_check = all(
                comp.symbol.split(":")[-1] in response.content 
                for comp in template.components if comp.required
            )
            result["validation"]["components_verified"] = component_check
            
            # Check for power rail definitions
            power_check = all(
                rail.lower() in response.content.lower()
                for rail in template.power_rails
            )
            result["validation"]["connections_valid"] = power_check
        
        return result
    
    def _update_stats(
        self,
        pattern_type: PatternType,
        latency_ms: float,
        success: bool
    ):
        """Update generation statistics"""
        stats = self.generation_stats
        
        stats["total_generated"] += 1
        
        # Update average latency
        total = stats["total_generated"]
        current_avg = stats["avg_latency_ms"]
        stats["avg_latency_ms"] = ((current_avg * (total - 1)) + latency_ms) / total
        
        # Update success rate
        if success:
            success_count = int(stats["success_rate"] * (total - 1)) + 1
        else:
            success_count = int(stats["success_rate"] * (total - 1))
        
        stats["success_rate"] = success_count / total
        
        # Update pattern usage
        pattern_name = pattern_type.value
        if pattern_name not in stats["pattern_usage"]:
            stats["pattern_usage"][pattern_name] = 0
        stats["pattern_usage"][pattern_name] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return self.generation_stats.copy()
    
    def list_available_patterns(self) -> List[Dict[str, Any]]:
        """List all available circuit patterns"""
        return self.patterns.list_patterns()
    
    async def generate_demo_circuits(self) -> Dict[str, Any]:
        """Generate demo circuits for all major patterns"""
        demo_patterns = [
            PatternType.ESP32_BASIC,
            PatternType.STM32_BASIC,
            PatternType.MOTOR_STEPPER,
            PatternType.SENSOR_IMU,
            PatternType.LED_NEOPIXEL
        ]
        
        results = {}
        
        for pattern in demo_patterns:
            try:
                result = await self.generate_circuit(pattern)
                results[pattern.value] = result
                logger.info(f"✅ Generated demo: {pattern.value}")
                
            except Exception as e:
                logger.error(f"❌ Demo failed for {pattern.value}: {e}")
                results[pattern.value] = {"success": False, "error": str(e)}
        
        return results
    
    def generate_hierarchical_project(
        self,
        project_type: str,
        output_dir: Path,
        project_name: str = None
    ) -> Dict[str, Any]:
        """
        Generate complete hierarchical project with separate subcircuit files
        
        Args:
            project_type: Type of project ("esp32_complete_board", "stm32_complete_board")
            output_dir: Directory to create project in
            project_name: Name for the project directory (defaults to project_type)
            
        Returns:
            Dict with success status and project information
        """
        try:
            if project_name is None:
                project_name = project_type
            
            project_path = output_dir / project_name
            success = self.project_generator.generate_project(project_type, output_dir, project_name)
            
            if success:
                return {
                    "success": True,
                    "project_path": str(project_path),
                    "project_type": project_type,
                    "files_created": self._count_project_files(project_path),
                    "message": f"✅ Hierarchical project '{project_name}' created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to generate project type: {project_type}",
                    "message": f"❌ Project generation failed"
                }
                
        except Exception as e:
            logger.error(f"❌ Hierarchical project generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ Exception during project generation: {e}"
            }
    
    def _count_project_files(self, project_path: Path) -> int:
        """Count files created in the project"""
        try:
            if project_path.exists():
                return len([f for f in project_path.iterdir() if f.is_file()])
            return 0
        except Exception:
            return 0
    
    def list_available_project_types(self) -> List[str]:
        """List available hierarchical project types"""
        return list(self.project_generator.templates.keys())