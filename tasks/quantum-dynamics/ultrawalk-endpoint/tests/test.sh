#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mkdir -p /logs/verifier

if python3 "$DIR/test_outputs.py"; then
    echo '{"reward": 1.0}' > /logs/verifier/reward.json
    echo "1.0" > /logs/verifier/reward.txt
    echo "Tests executed successfully."
else
    echo '{"reward": 0.0}' > /logs/verifier/reward.json
    echo "0.0" > /logs/verifier/reward.txt
    echo "Tests failed."
fi
