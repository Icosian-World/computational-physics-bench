#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mkdir -p /logs/verifier

if python3 "$DIR/test_outputs.py"; then
    echo "Verifier rubric passed with full reward."
else
    status=$?
    if [ ! -f /logs/verifier/reward.json ]; then
        echo '{"reward": 0.0}' > /logs/verifier/reward.json
        echo "0.0" > /logs/verifier/reward.txt
        echo '{"reward": 0.0, "details": [{"name": "verifier", "earned": 0.0, "possible": 1.0, "message": "test_outputs.py failed before writing reward"}]}' > /logs/verifier/rubric_details.json
    fi
    echo "Verifier rubric completed with partial or zero reward."
    exit "$status"
fi
