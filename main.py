"""
GeneFlow: ADK-Powered Bioinformatics Copilot

Main entry point for launching the GeneFlow application. Performs dependency checks,
environment validation, and launches the Streamlit UI.

Usage:
    python main.py
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """
    Verifies all required Python packages are installed.
    
    Checks for:
        - streamlit: Web UI framework
        - google.generativeai: AI API client
        - Bio (Biopython): Sequence analysis
        - pandas, plotly: Data visualization
        - pydantic, tiktoken, psutil: Support libraries
    
    Returns:
        bool: True if all packages installed, False otherwise
    
    Note:
        Logs missing packages and suggests pip install command
    """
    required_packages = [
        'streamlit',
        'google.generativeai',
        'Bio',
        'pandas',
        'plotly',
        'pydantic',
        'tiktoken',
        'psutil'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.split('.')[0])
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"Missing required packages: {', '.join(missing)}")
        logger.error("Please run: pip install -r requirements.txt")
        return False
    
    return True


def check_environment():
    """
    Validates environment configuration and creates necessary directories.
    
    Checks:
        - GOOGLE_API_KEY environment variable
    
    Creates:
        - sessions/: Session storage
        - metrics/: Performance metrics
        - geneflow_plots/: Visualization outputs
    
    Returns:
        bool: Always True (warnings only)
    """
    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY not found in environment variables")
        logger.warning("You will need to provide it in the UI or set it in .env file")
    
    # Create necessary directories
    Path("sessions").mkdir(exist_ok=True)
    Path("metrics").mkdir(exist_ok=True)
    Path("geneflow_plots").mkdir(exist_ok=True)
    
    return True


def launch_ui():
    """
    Launches the Streamlit web interface.
    
    Starts Streamlit server with Home.py as entry point.
    
    Returns:
        bool: True on successful launch, False if UI file not found
    """
    logger.info("Launching GeneFlow UI...")
    ui_path = os.path.join(os.path.dirname(__file__), "src", "ui", "Home.py")
    
    if not os.path.exists(ui_path):
        logger.error(f"UI file not found: {ui_path}")
        return False
    
    os.system(f'streamlit run "{ui_path}"')
    return True


def main():
    """
    Main application entry point.
    
    Workflow:
        1. Print welcome banner
        2. Check dependencies
        3. Validate environment
        4. Launch Streamlit UI
    
    Exits with code 1 if checks fail.
    """
    print("=" * 60)
    print("🧬 GeneFlow: ADK-Powered Bioinformatics Copilot")
    print("=" * 60)
    print()
    
    logger.info("Starting GeneFlow application...")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Please install required packages.")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Please configure properly.")
        sys.exit(1)
    
    # Launch UI
    logger.info("All checks passed. Launching UI...")
    print()
    print("📱 Opening GeneFlow UI in your browser...")
    print("💡 If the browser doesn't open automatically, go to: http://localhost:8501")
    print()
    
    launch_ui()


if __name__ == "__main__":
    main()
