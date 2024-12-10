import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import os

from main import setup_cerebras_client, generate_response, print_response, main

class TestMain(unittest.TestCase):

    def test_setup_cerebras_client(self):
        from main import Cerebras
        mock_cerebras = MagicMock(spec=Cerebras)
        os.environ['API_KEY'] = 'fake-api-key'
        with patch('main.Cerebras', return_value=mock_cerebras):
            client = setup_cerebras_client()
            self.assertEqual(client, mock_cerebras)

    @patch('main.Cerebras')
    def test_generate_response(self, mock_cerebras):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Test response"))
        ]

        chat_history = [{"role": "system", "content": "You are a helpful assistant."}]
        prompt = "Test prompt"

        response = generate_response(mock_client, prompt, chat_history)

        mock_client.chat.completions.create.assert_called_once_with(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            model="llama3.1-70b"
        )

        self.assertEqual(response, mock_client.chat.completions.create.return_value)

    @patch('builtins.print')
    @patch('time.sleep')
    def test_print_response(self, mock_sleep, mock_print):
        mock_response = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))],
            usage=MagicMock(total_tokens=10),
            time_info=MagicMock(total_time=1)
        )

        print_response(mock_response)

        mock_print.assert_any_call("(Tokens per second: 10.00)")

    @patch('main.setup_cerebras_client')
    @patch('main.generate_response')
    @patch('main.print_response')
    @patch('builtins.input', side_effect=['Test input', 'exit()'])
    def test_main(self, mock_input, mock_print_response, mock_generate_response, mock_setup_client):
        mock_client = MagicMock()
        mock_setup_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_generate_response.return_value = mock_response

        captured_output = StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__
        actual_output = captured_output.getvalue().strip()

        self.assertIn("Welcome to llama3.1-70b Text Generator made by (Awan)", actual_output)
        self.assertIn("Happy chat and talk with your llama3.1-70b AI Generative Model", actual_output)
        self.assertIn("Addhe Warman Putra - (Awan)", actual_output)
        self.assertIn("Type 'exit()' to exit from program", actual_output)

        expected_chat_history = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "assistant", "content": "Test response"}
        ]

        mock_generate_response.assert_called_once_with(mock_client, "Test input", expected_chat_history)
        mock_print_response.assert_called_once_with(mock_response)

if __name__ == '__main__':
    unittest.main()