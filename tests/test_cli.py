"""Tests for Typer CLI commands."""
from typer.testing import CliRunner
from hw_assistant.cli import app

runner = CliRunner()


def test_cli_ask_mock():
    result = runner.invoke(app, ["ask", "Can I upgrade my RAM?", "--mock"])
    assert result.exit_code == 0
    assert "RAM Topology" in result.output
    assert "64 GB" in result.output


def test_cli_inspect_mock():
    result = runner.invoke(app, ["inspect", "--mock"])
    assert result.exit_code == 0
    assert "Hardware Specification Report" in result.output
    assert "Processor" in result.output
    assert "Physical Memory" in result.output
    assert "Storage Drives" in result.output


def test_cli_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "System Capability & Security Diagnosis" in result.output
    assert "Operating System" in result.output
