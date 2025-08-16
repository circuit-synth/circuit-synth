"""
Fast Circuit Generation Setup
Install dependencies for Google ADK and OpenRouter integration
"""

import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Install required dependencies for fast generation"""
    dependencies = [
        "google-adk>=0.1.0",  # Google Agent Development Kit
        "openai>=1.0.0",      # For OpenRouter API compatibility
        "python-dotenv>=1.0.0",  # Environment variable management
        "asyncio",            # Async support
        "aiofiles>=23.0.0",   # Async file operations
    ]
    
    print("🚀 Installing fast generation dependencies...")
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    return True

def create_env_template():
    """Create environment template file"""
    env_template = """# Fast Generation API Keys
# OpenRouter API Key (required)
OPENROUTER_API_KEY=your_openrouter_key_here

# Google Cloud Project Settings (optional, for direct Vertex AI)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# Model Configuration
DEFAULT_FAST_MODEL=google/gemini-2.5-flash
FALLBACK_MODEL=google/gemini-2.0-flash-experimental
"""
    
    env_path = Path("/Users/shanemattner/Desktop/circuit-synth2/.env.template")
    env_path.write_text(env_template)
    print(f"📝 Created environment template: {env_path}")

def main():
    """Main setup function"""
    print("🎛️ Circuit-Synth Fast Generation Setup")
    print("=" * 50)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return 1
    
    # Create environment template
    create_env_template()
    
    print("\n✅ Fast generation setup complete!")
    print("\n📋 Next steps:")
    print("1. Copy .env.template to .env")
    print("2. Add your OpenRouter API key")
    print("3. Test with: python -m circuit_synth.fast_generation.demo")
    
    return 0

if __name__ == "__main__":
    exit(main())