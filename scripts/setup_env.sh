#!/bin/bash

# FINBOT Setup & Cleanup Script for Phase 1 Build
# This script verifies the environment, sets up a virtual environment,
# cleans up specified files and directories, resets databases, and creates configuration skeletons.

echo "Starting FINBOT environment setup and cleanup..."

# Environment Verification
echo "Verifying environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+\.\d+')
if [[ "$python_version" == "3.11.9" ]]; then
    echo "Python version: $python_version"
else
    echo "Warning: Python version is $python_version, expected 3.11.9"
fi

# Check Node.js version
node_version=$(node --version 2>&1 | grep -oP '\d+\.\d+\.\d+')
if [[ "$node_version" =~ ^18\. ]]; then
    echo "Node.js version: $node_version"
else
    echo "Warning: Node.js version is $node_version, expected 18.x"
fi

# Virtual Environment Setup
echo "Checking virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created. Activate with: source venv/bin/activate"
else
    echo "Virtual environment already exists."
fi

# File Cleanup (The "Purge")
echo "Performing file cleanup..."
files_to_remove=("task.md" "testingissues.md" "fix_TODO.md" "pytest_output.txt" "notes/")
for file in "${files_to_remove[@]}"; do
    if [ -e "$file" ]; then
        rm -rf "$file"
        echo "Removed $file"
    fi
done

# Database Reset
echo "Resetting databases..."
databases_to_remove=("test.db" "market_data.db")
for db in "${databases_to_remove[@]}"; do
    if [ -f "$db" ]; then
        rm "$db"
        echo "Removed $db"
    fi
done

# Configuration Skeleton
echo "Setting up configuration files..."
if [ ! -f ".env" ]; then
    touch .env
    echo "Created empty .env file"
fi

if [ ! -f "frontend/.env" ]; then
    echo "VITE_API_BASE_URL=http://localhost:8000" > frontend/.env
    echo "Created frontend/.env with default VITE_API_BASE_URL"
fi

echo "FINBOT environment setup and cleanup completed."
