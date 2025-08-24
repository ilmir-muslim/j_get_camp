#!/bin/bash

find . -type d -name "__pycache__" -exec rm -rf {} +
echo "Все __pycache__ удалены."
