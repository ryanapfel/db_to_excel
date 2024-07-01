# tests/test_script.py

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from excel_output.cli import cli

# Mocking os.makedirs to avoid creating directories during tests
@patch("os.makedirs")
# Mocking the EmailClient to avoid sending real emails during tests
@patch("src.EmailClient.EmailClient.send")
def test_users_command(mock_send, mock_makedirs):
    # Mock the methods that are supposed to write to the filesystem
    mock_makedirs.return_value = None
    mock_send.return_value = None

    runner = CliRunner()
    result = runner.invoke(cli, ['send', '--study', 'test_study', '--to', 'test@example.com'])
    assert result.exit_code == 0

    # Check if the mocks were called as expected
    mock_makedirs.assert_called()
    mock_send.assert_called_once_with('test@example.com', 'Updated Core Lab Tracker -- test_study', MagicMock(), attachments=['test_study_tracker.xlsx'])

    # Uncomment and modify the following line based on your expected output
    # assert "expected output" in result.output