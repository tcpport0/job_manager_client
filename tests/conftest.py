import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)

