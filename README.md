# 🧠 Cerebras CLI - AI-Powered Command-Line Interface

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful, modern command-line interface for interacting with Cerebras AI models. Inspired by Gemini CLI and built with Python, this tool provides an intuitive and extensible platform for AI-assisted development workflows.

## Features
* Utilizes the Cerebras LLaMA 3.1 70B model
* Interactive command-line interface
* Real-time response generation
* Performance metrics display (tokens per second)
* Typewriter-style output for responses

## Prerequisites
* Python 3.6+
* Cerebras Cloud SDK
* Cerebras API Key

## Installation
1. Clone this repository or download the main.py file.
2. Install the required dependencies:
```
pip install cerebras-cloud-sdk
```
3. Set up your Cerebras API Key as an environment variable:
```
export CEREBRAS_API_KEY=your_api_key_here
export CEREBRAS_MODEL_ID=your_model_id_here
export CEREBRAS_SYSTEM_MESSAGE="Your custom system message here"
export CHAR_DELAY=0.03
```

# Usage
Run the script using Python:
```
python main.py
```

* The application will start and display a welcome message.
* Enter your prompts at the > prompt.
* The AI will generate and display responses.
* Type exit() to quit the application.

# Code Structure
* ```setup_cerebras_client()```: Sets up the Cerebras client using the API key.
* ```generate_response()```: Generates a response using the Cerebras model.
* ```print_response()```: Prints the AI's response with a typewriter effect and displays performance metrics.
* ```main()```: The main function that runs the chat loop.

# Author
Addhe Warman Putra (Awan)

# License
This project is open-source and available under the MIT License.

# Disclaimer
This application requires a valid Cerebras API key and access to the Cerebras Cloud platform. Make sure you have the necessary permissions and subscriptions before using this application.