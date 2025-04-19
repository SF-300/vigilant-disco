#!/bin/bash

# Script to install dependencies for the Anki Addon Frontend project

echo "Updating package lists..."
sudo apt update

echo "Installing uv (Python dependency manager)..."
pip install uv

echo "Installing PyQt development tools..."
sudo apt install -y python3-pyqt5 pyqt5-dev-tools

echo "Installing build essentials (optional, for compiling dependencies)..."
sudo apt install -y build-essential

echo "Install uv dependencies..."
uv install --dev

echo "All dependencies have been installed successfully!"