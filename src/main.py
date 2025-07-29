#!/usr/bin/env python3
"""
Cerebras ChatGPT CLI - Enhanced version with modern architecture.

This module provides both the legacy interface and the new modular CLI.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add cerebras_cli to path if it exists
project_root = Path(__file__).parent.parent
cerebras_cli_path = project_root / "cerebras_cli"

if cerebras_cli_path.exists():
    sys.path.insert(0, str(project_root))
    
    try:
        # Try to use the new CLI
        from cerebras_cli.cli.main import main as new_main
        HAS_NEW_CLI = True
    except ImportError:
        HAS_NEW_CLI = False
else:
    HAS_NEW_CLI = False

# Legacy imports
from cerebras.cloud.sdk import Cerebras

# Import legacy configuration
try:
    from config import MODEL_ID, SYSTEM_MESSAGE, API_KEY, CHAR_DELAY
except ImportError:
    # Default configuration if config.py is not available
    MODEL_ID = os.getenv("CEREBRAS_MODEL_ID", "llama-4-scout-17b-16e-instruct")
    API_KEY = os.getenv("CEREBRAS_API_KEY")
    CHAR_DELAY = float(os.getenv("CHAR_DELAY", "0.02"))
    SYSTEM_MESSAGE = {
        "role": "system",
        "content": os.getenv("CEREBRAS_SYSTEM_MESSAGE", "You are a helpful assistant.")
    }


def check_new_cli_available() -> bool:
    """Check if the new CLI system is available."""
    return HAS_NEW_CLI and cerebras_cli_path.exists()


def setup_cerebras_client() -> Cerebras:
    """Setup Cerebras client with error handling."""
    global cerebras_client
    
    if not API_KEY:
        print("❌ Error: Missing Cerebras API Key.")
        print("\nPlease set your API key using one of these methods:")
        print("1. Environment variable: export CEREBRAS_API_KEY=your_key")
        print("2. Create a .env file with: CEREBRAS_API_KEY=your_key")
        print("3. Set it in config.py")
        sys.exit(1)

    if cerebras_client is None:
        cerebras_client = Cerebras(api_key=API_KEY)
    
    return cerebras_client


def generate_response(
    client: Cerebras,
    prompt: str,
    chat_history: List[Dict[str, str]]
) -> Optional[Any]:
    """Generate response using Cerebras API."""
    chat_history.append({"role": "user", "content": prompt})
    try:
        return client.chat.completions.create(
            messages=chat_history,
            model=MODEL_ID,
        )
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return None


def print_response(response: Optional[Any]) -> None:
    """Print response with typewriter effect."""
    if response is None:
        print("❌ Failed to generate a response.")
        return

    message: str = response.choices[0].message.content
    
    # Print with character delay for typewriter effect
    for char in message:
        print(char, end="", flush=True)
        if CHAR_DELAY > 0:
            import time
            time.sleep(CHAR_DELAY)
    print()

    # Show usage statistics
    if hasattr(response, 'usage') and hasattr(response, 'time_info'):
        total_tokens: int = response.usage.total_tokens
        total_time: float = response.time_info.total_time
        tokens_per_second: float = total_tokens / max(total_time, 0.001)
        print(f"💡 Tokens: {total_tokens} | Time: {total_time:.2f}s | Speed: {tokens_per_second:.2f} tokens/s")


def get_welcome_text() -> str:
    """Get welcome message."""
    new_cli_status = "✅ Available" if check_new_cli_available() else "❌ Not installed"
    
    return f"""
🧠 Welcome to Cerebras CLI v1.0.0
╭─────────────────────────────────────────────────╮
│ AI-powered command-line interface              │
│ Model: {MODEL_ID:<38} │
│ Enhanced CLI: {new_cli_status:<30} │
╰─────────────────────────────────────────────────╯

💡 Available modes:
   • Interactive mode (current)
   • Enhanced CLI (run: python -m cerebras_cli.cli.main)
   
🎯 Commands:
   • Type 'exit()' to quit
   • Type '/help' for enhanced features (if available)
   • Type '@filename' to include file content
   
👨‍💻 Made by Addhe Warman Putra (Awan)
"""


def handle_command(command: str, chat_history: List[Dict[str, str]]) -> bool:
    """Handle special commands. Returns True if command was handled."""
    command = command.strip().lower()
    
    if command == "/help":
        help_text = """
🆘 Available Commands:
   
📝 Basic Commands:
   • exit() - Exit the program
   • /help - Show this help message
   • /clear - Clear conversation history
   • /history - Show conversation history
   
📁 File Operations:
   • @filename - Include file content in your message
   • @*.py - Include all Python files (be careful with large projects)
   
⚙️  Configuration:
   • /config - Show current configuration
   • /model - Show current model information
   
🚀 Enhanced Features:
   Run 'python -m cerebras_cli.cli.main' for the full featured CLI with:
   • Rich terminal UI
   • Advanced configuration management
   • Tools system
   • Better file handling
   • Conversation save/load
        """
        print(help_text)
        return True
    
    elif command == "/clear":
        os.system('clear' if os.name == 'posix' else 'cls')
        chat_history.clear()
        chat_history.append(SYSTEM_MESSAGE)
        print("🧹 Conversation history cleared")
        return True
    
    elif command == "/history":
        print(f"\n📜 Conversation History ({len(chat_history)-1} messages):")
        for i, msg in enumerate(chat_history[1:], 1):  # Skip system message
            role = msg['role'].title()
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"   {i}. {role}: {content}")
        print()
        return True
    
    elif command == "/config":
        print(f"""
⚙️  Current Configuration:
   • Model: {MODEL_ID}
   • Character Delay: {CHAR_DELAY}s
   • API Key: {'✅ Set' if API_KEY else '❌ Not set'}
   • Enhanced CLI: {'✅ Available' if check_new_cli_available() else '❌ Not installed'}
        """)
        return True
    
    elif command == "/model":
        print(f"""
🤖 Model Information:
   • Current Model: {MODEL_ID}
   • Provider: Cerebras
   • Type: Large Language Model
   
Available Models:
   • llama-4-scout-17b-16e-instruct (current default)
   • llama-3.1-8b-instruct
   • llama-3.1-70b-instruct
   
To change model: set CEREBRAS_MODEL_ID environment variable
        """)
        return True
    
    return False


def handle_file_include(user_input: str) -> str:
    """Handle @filename includes."""
    if not user_input.startswith('@'):
        return user_input
    
    parts = user_input[1:].split(' ', 1)
    filename = parts[0]
    additional_text = parts[1] if len(parts) > 1 else ""
    
    try:
        file_path = Path(filename)
        
        if '*' in filename:
            # Handle glob patterns
            import glob
            matching_files = glob.glob(filename)
            if not matching_files:
                print(f"❌ No files found matching pattern: {filename}")
                return ""
            
            combined_content = ""
            for file in matching_files[:5]:  # Limit to 5 files
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    combined_content += f"\n--- File: {file} ---\n{content}\n"
                except Exception as e:
                    print(f"⚠️  Could not read {file}: {e}")
            
            context = f"Multiple files:\n{combined_content}"
            if additional_text:
                context += f"\n\nQuestion: {additional_text}"
            
            print(f"📁 Included {len(matching_files)} file(s)")
            return context
        
        else:
            # Handle single file
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                return ""
            
            if not file_path.is_file():
                print(f"❌ Not a file: {filename}")
                return ""
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            context = f"File: {filename}\n```\n{content}\n```"
            if additional_text:
                context += f"\n\n{additional_text}"
            
            print(f"📁 Included file: {filename} ({len(content)} characters)")
            return context
            
    except Exception as e:
        print(f"❌ Error reading file {filename}: {e}")
        return ""


def legacy_main() -> None:
    """Main function for legacy mode."""
    try:
        client = setup_cerebras_client()
        chat_history: List[Dict[str, str]] = [SYSTEM_MESSAGE]

        print(get_welcome_text())

        while True:
            try:
                user_input: str = input("🤖 > ").strip()
                
                if user_input.lower() == "exit()":
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if handle_command(user_input, chat_history):
                        continue
                
                # Handle file includes
                if user_input.startswith('@'):
                    user_input = handle_file_include(user_input)
                    if not user_input:
                        continue
                
                # Generate and print response
                response: Optional[Any] = generate_response(client, user_input, chat_history)
                if response:
                    chat_history.append({
                        "role": "assistant",
                        "content": response.choices[0].message.content
                    })
                    print_response(response)
                else:
                    print("❌ Failed to generate a response. Please try again.")

            except KeyboardInterrupt:
                print("\n⚠️  Interrupted. Type 'exit()' to quit or continue chatting...")
                continue

    except KeyboardInterrupt:
        print("\n👋 Program interrupted by user. Exiting...")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


def main() -> None:
    """Main entry point with CLI selection."""
    # Check command line arguments for new CLI preference
    if "--new-cli" in sys.argv or "--enhanced" in sys.argv:
        if check_new_cli_available():
            print("🚀 Starting enhanced Cerebras CLI...")
            new_main()
            return
        else:
            print("❌ Enhanced CLI not available. Install requirements first:")
            print("   pip install -r requirements.txt")
            print("   Falling back to legacy mode...\n")
    
    # Check if new CLI is available and no specific mode requested
    if check_new_cli_available() and len(sys.argv) == 1:
        print("🎯 Multiple CLI modes available:")
        print("   1. Legacy mode (current)")
        print("   2. Enhanced mode (recommended)")
        
        try:
            choice = input("\nSelect mode (1/2) or press Enter for legacy: ").strip()
            if choice == "2":
                print("🚀 Starting enhanced Cerebras CLI...")
                new_main()
                return
        except KeyboardInterrupt:
            print("\n")
    
    # Run legacy CLI
    legacy_main()


if __name__ == "__main__":
    main()
