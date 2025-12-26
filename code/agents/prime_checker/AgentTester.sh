#!/bin/bash

# Function to run a test case
run_test() {
    local test_name="$1"
    local number="$2"
    local expected_status="$3"
    local expected_json_str="$4"

    echo "Running test: $test_name"
    
    local payload
    if [ "$test_name" == "Missing Number Field" ]; then
        payload='{}'
    else
        payload=$(printf '{"number": "%s"}' "$number")
    fi

    body_file=$(mktemp)
    # Corrected curl command: removed the erroneous backslash before http_code
    status_code=$(curl -s -w "%{http_code}" -o "$body_file" -X POST -H "Content-Type: application/json" -d "$payload" http://localhost:5000/isprime)
    json_response=$(cat "$body_file")
    rm "$body_file"

    if [ "$status_code" -ne "$expected_status" ]; then
        echo "  [FAIL] Expected status $expected_status, but got $status_code"
        echo "  Response body: $json_response"
        return 1
    fi

    # Compare only the fields present in the expected JSON (ignore extra fields).
    expected_json=$(echo "$expected_json_str" | jq .)
    actual_json=$(echo "$json_response" | jq .)

    for key in $(echo "$expected_json" | jq -r 'keys[]'); do
        expected_val=$(echo "$expected_json" | jq -c ".\"$key\"")
        actual_val=$(echo "$actual_json" | jq -c ".\"$key\"")
        if [ "$expected_val" != "$actual_val" ]; then
            echo "  [FAIL] JSON mismatch for key '$key'."
            echo "  Expected: $expected_val"
            echo "  Got:      $actual_val"
            return 1
        fi
    done

    echo "  [PASS]"
    return 0
}

# --- Test Cases ---
failures=0

# Valid Inputs
run_test "Small Prime (2)" "2" 200 '{"is_prime": true}' || ((failures++))
run_test "Small Prime (7)" "7" 200 '{"is_prime": true}' || ((failures++))
run_test "Large Prime" "2441" 200 '{"is_prime": true}' || ((failures++))
run_test "Small Composite (4)" "4" 200 '{"is_prime": false, "factors": ["2", "2"]}' || ((failures++))
run_test "Large Composite" "100" 200 '{"is_prime": false, "factors": ["2", "2", "5", "5"]}' || ((failures++))

# Invalid Inputs
run_test "Negative Number" "-10" 400 '{"error": "Input must contain only digits"}' || ((failures++))
run_test "Zero" "0" 400 '{"error": "Zero is neither prime nor composite"}' || ((failures++))
run_test "Non-numeric String" "abc" 400 '{"error": "Input must contain only digits"}' || ((failures++))
run_test "Empty Number" "" 400 '{"error": "Input must contain only digits"}' || ((failures++))
run_test "Missing Number Field" "N/A" 400 "{\"error\": \"Missing 'number' field in JSON payload\"}" || ((failures++))


# --- Summary ---
if [ "$failures" -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "$failures tests failed."
    exit 1
fi
