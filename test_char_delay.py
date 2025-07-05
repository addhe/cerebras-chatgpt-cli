#!/usr/bin/env python3
"""
Quick test script to verify char_delay is working correctly.
"""

import asyncio
from cerebras_cli.core.config import Config

def test_char_delay_config():
    """Test that char_delay is now 0.0 by default."""
    config = Config()
    print(f"Default char_delay: {config.cli.char_delay}")
    
    # Test environment variable override
    import os
    os.environ['CEREBRAS_CHAR_DELAY'] = '0.05'
    config = Config()
    print(f"With env var CEREBRAS_CHAR_DELAY=0.05: {config.cli.char_delay}")
    
    # Clean up
    del os.environ['CEREBRAS_CHAR_DELAY']
    
    # Test back to default
    config = Config()
    print(f"Back to default: {config.cli.char_delay}")
    
    assert config.cli.char_delay == 0.0, f"Expected 0.0, got {config.cli.char_delay}"
    print("✅ char_delay test passed!")

if __name__ == "__main__":
    test_char_delay_config()
