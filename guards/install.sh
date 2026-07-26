#!/bin/bash
# Install leak-gate hooks into .git/hooks (run after every fresh clone).
cd "$(git rev-parse --show-toplevel)" || exit 1
cp guards/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
cp guards/pre-push  .git/hooks/pre-push  && chmod +x .git/hooks/pre-push
echo "guards installed"
