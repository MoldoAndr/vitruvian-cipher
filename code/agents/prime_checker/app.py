from flask import Flask, request, jsonify
import subprocess
import re
import logging
import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='/app/prime_checker.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Also log to console for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


def is_valid_number(number_str):
    """Validate that the input is a positive integer greater than 1."""
    try:
        # Check if it's a valid integer format
        if not re.match(r'^\d+$', str(number_str)):
            return False, "Input must contain only digits"
        
        # Convert to integer and check range
        num = int(number_str)
        
        if num < 2:
            if num == 0:
                return False, "Zero is neither prime nor composite"
            elif num == 1:
                return False, "One is neither prime nor composite by definition"
            else:
                return False, "Negative numbers are not valid"
        
        # Check for reasonable upper limit to prevent abuse
        if num > 10**1000:
            return False, "Number too large (max 10^1000)"
            
        return True, None
        
    except (ValueError, OverflowError) as e:
        return False, f"Invalid number format: {str(e)}"


def create_robust_session():
    """Create a requests session with retry strategy and proper timeouts."""
    session = requests.Session()
    
    # Define retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Wait time between retries (1, 2, 4 seconds)
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        allowed_methods=["GET"]  # Only retry on GET requests
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def test_factordb_connection():
    """Test FactorDB connectivity with a known prime number."""
    try:
        session = create_robust_session()
        # Test with a known small prime (17)
        test_url = "https://factordb.com/api?query=17"
        
        response = session.get(test_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Verify the response format
        if not isinstance(data, dict):
            logging.error("FactorDB test: Response is not a dictionary")
            return False
            
        if 'status' not in data:
            logging.error("FactorDB test: No 'status' field in response")
            return False
            
        # 17 should be prime (status 'P')
        if data.get('status') != 'P':
            logging.error(f"FactorDB test: Expected status 'P' for 17, got '{data.get('status')}'")
            return False
            
        logging.info("FactorDB connection test successful")
        return True
        
    except requests.exceptions.RequestException as e:
        logging.error(f"FactorDB connection test failed: {e}")
        return False
    except Exception as e:
        logging.error(f"FactorDB connection test error: {e}")
        return False


def run_yafu_command(command):
    """Run a YAFU command and capture output."""
    try:
        logging.debug(f"Running YAFU command: {command}")
        
        # Use stdin to pass the command to YAFU
        result = subprocess.run(
            ['/usr/local/bin/yafu'],
            input=command + '\n',
            capture_output=True,
            text=True,
            timeout=5,  # Increased timeout for larger numbers
            cwd='/opt/math/yafu'  # Set working directory to where yafu.ini is located
        )
        
        logging.debug(f"YAFU exit code: {result.returncode}")
        return result.stdout, result.stderr, result.returncode
        
    except subprocess.TimeoutExpired:
        logging.error(f"YAFU command timed out: {command}")
        return None, "Error: YAFU timed out", -1
    except FileNotFoundError:
        logging.error("YAFU binary not found at /usr/local/bin/yafu")
        return None, "Error: YAFU binary not found", -1
    except Exception as e:
        logging.error(f"YAFU command failed: {e}")
        return None, f"Error: {str(e)}", -1


def check_with_factordb(number):
    """Check primality and get factors using FactorDB API with robust error handling."""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            session = create_robust_session()
            url = f"https://factordb.com/api?query={number}"
            
            logging.debug(f"FactorDB attempt {attempt + 1}/{max_retries} for {number}")
            
            response = session.get(url, timeout=15)
            response.raise_for_status()
            
            # Validate response content type
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                raise ValueError(f"Invalid content type: {content_type}")
            
            data = response.json()
            
            # Validate response structure
            if not isinstance(data, dict):
                raise ValueError("Response is not a valid JSON object")
                
            if 'status' not in data:
                raise ValueError("Missing 'status' field in response")
            
            status = data.get("status", "").strip()
            
            # FactorDB status codes:
            # P = Prime
            # C = Composite (fully factored)
            # CF = Composite (partially factored)
            # U = Unknown
            # FF = Form factored
            
            if status == "P":
                logging.info(f"FactorDB: {number} is prime")
                return {"is_prime": True, "source": "factordb"}
                
            elif status in ["C", "CF", "FF"]:
                # Extract factors from the response
                factors = []
                factors_data = data.get("factors", [])
                
                if not isinstance(factors_data, list):
                    logging.warning(f"FactorDB: Invalid factors format for {number}")
                    return {"is_prime": False, "factors": [], "source": "factordb", "note": "Composite but factors unavailable"}
                
                for factor_info in factors_data:
                    if isinstance(factor_info, list) and len(factor_info) >= 1:
                        factor_value = str(factor_info[0]).strip()
                        if factor_value and factor_value.isdigit():
                            factors.append(factor_value)
                
                logging.info(f"FactorDB: {number} is composite with factors: {factors}")
                return {"is_prime": False, "factors": factors, "source": "factordb"}
                
            elif status == "U":
                logging.warning(f"FactorDB: Status unknown for {number}")
                return {"error": "FactorDB reports unknown status for this number", "source": "factordb"}
                
            else:
                logging.warning(f"FactorDB: Unexpected status '{status}' for {number}")
                return {"error": f"FactorDB returned unexpected status: {status}", "source": "factordb"}
                
        except requests.exceptions.Timeout:
            logging.warning(f"FactorDB timeout on attempt {attempt + 1} for {number}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logging.info(f"Retrying FactorDB in {delay} seconds...")
                time.sleep(delay)
                continue
            return {"error": "FactorDB request timed out after multiple attempts"}
            
        except requests.exceptions.RequestException as e:
            logging.error(f"FactorDB request error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logging.info(f"Retrying FactorDB in {delay} seconds...")
                time.sleep(delay)
                continue
            return {"error": f"FactorDB request failed: {str(e)}"}
            
        except (ValueError, KeyError) as e:
            logging.error(f"FactorDB response parsing error: {e}")
            return {"error": f"FactorDB response parsing failed: {str(e)}"}
            
        except Exception as e:
            logging.error(f"Unexpected FactorDB error: {e}")
            return {"error": f"FactorDB unexpected error: {str(e)}"}
    
    return {"error": "FactorDB failed after all retry attempts"}


def parse_yafu_factors(stdout):
    """Parse factors from YAFU factorization output."""
    factors = []
    lines = stdout.split('\n')
    
    for line in lines:
        line = line.strip()
        # Look for lines like "Pxx = nnn" or "PRPxx = nnn" where nnn is a factor
        match = re.search(r'^(PRP|P)(\d+)\s*=\s*(\d+)', line)
        if match:
            factor = match.group(3)
            factors.append(factor)
            logging.debug(f"Found factor: {factor} (type: {match.group(1)}{match.group(2)})")
    
    # Also look for other factor formats YAFU might use
    for line in lines:
        line = line.strip()
        # Look for "***factors found***" section
        if "factor:" in line.lower():
            match = re.search(r'factor:\s*(\d+)', line, re.IGNORECASE)
            if match:
                factor = match.group(1)
                if factor not in factors:
                    factors.append(factor)
                    logging.debug(f"Found additional factor: {factor}")
    
    return factors


@app.route('/isprime', methods=['POST'])
def check_prime():
    """Handle POST requests to check if a number is prime."""
    try:
        data = request.get_json()
        if not data or 'number' not in data:
            logging.error("Invalid request: 'number' field missing")
            return jsonify({"error": "Missing 'number' field in JSON payload"}), 400

        number = str(data['number']).strip()
        
        # Validate input
        is_valid, error_msg = is_valid_number(number)
        if not is_valid:
            logging.error(f"Invalid input: {number} - {error_msg}")
            return jsonify({"error": error_msg}), 400

        logging.info(f"Processing primality check for: {number}")

        # First try YAFU for primality check
        logging.info(f"Checking primality of {number} using YAFU")
        stdout, stderr, returncode = run_yafu_command(f"isprime({number})")
        
        yafu_failed = False
        
        if returncode != 0 or not stdout:
            yafu_failed = True
            if stderr:
                logging.error(f"YAFU failed for isprime({number}): {stderr}")
            else:
                logging.error(f"YAFU returned no output for isprime({number})")
        elif stderr:
            # YAFU had warnings but might still have useful output
            logging.warning(f"YAFU stderr for isprime({number}): {stderr}")

        if not yafu_failed and stdout:
            # Log raw YAFU output for debugging
            logging.debug(f"YAFU isprime({number}) output:\n{stdout}")

            # Parse primality result from YAFU
            # YAFU isprime returns "ans = 1" for prime, "ans = 0" for composite
            is_prime = "ans = 1" in stdout
            is_composite = "ans = 0" in stdout

            if is_prime:
                logging.info(f"YAFU: {number} is prime")
                return jsonify({"is_prime": True, "source": "yafu"})
            
            if is_composite:
                # Number is composite, now factor it with YAFU
                logging.info(f"YAFU: {number} is composite, attempting factorization")
                factor_stdout, factor_stderr, factor_returncode = run_yafu_command(f"factor({number})")
                
                if factor_returncode == 0 and factor_stdout:
                    if factor_stderr:
                        logging.warning(f"YAFU factorization stderr for {number}: {factor_stderr}")
                    
                    # Log raw YAFU factorization output for debugging
                    logging.debug(f"YAFU factor({number}) output:\n{factor_stdout}")

                    # Parse factors from YAFU output
                    factors = parse_yafu_factors(factor_stdout)
                    
                    if factors:
                        logging.info(f"YAFU: {number} is composite, factors: {factors}")
                        return jsonify({"is_prime": False, "factors": factors, "source": "yafu"})
                    else:
                        logging.warning(f"Could not parse factors from YAFU output for {number}")
                else:
                    logging.error(f"YAFU factorization failed for {number}: {factor_stderr}")

        # YAFU failed or didn't give a definitive answer, fall back to FactorDB
        logging.info(f"Falling back to FactorDB for {number}")
        result = check_with_factordb(number)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Unexpected error in check_prime: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with FactorDB connectivity test."""
    health_status = {
        "status": "healthy",
        "yafu_available": os.path.exists('/usr/local/bin/yafu'),
        "factordb_accessible": test_factordb_connection(),
        "timestamp": time.time()
    }
    
    # Determine overall health
    if not health_status["yafu_available"] and not health_status["factordb_accessible"]:
        health_status["status"] = "unhealthy"
        return jsonify(health_status), 503
    elif not health_status["yafu_available"]:
        health_status["status"] = "degraded"
        health_status["note"] = "YAFU unavailable, using FactorDB only"
    elif not health_status["factordb_accessible"]:
        health_status["status"] = "degraded"
        health_status["note"] = "FactorDB unavailable, using YAFU only"
    
    return jsonify(health_status)


@app.route('/test-factordb', methods=['GET'])
def test_factordb_endpoint():
    """Dedicated endpoint to test FactorDB connectivity."""
    test_numbers = [17, 21, 97]  # Known prime, composite, prime
    results = {}
    
    for num in test_numbers:
        logging.info(f"Testing FactorDB with number: {num}")
        result = check_with_factordb(str(num))
        results[str(num)] = result
    
    return jsonify({
        "factordb_test_results": results,
        "overall_status": "pass" if all("error" not in r for r in results.values()) else "fail"
    })


if __name__ == '__main__':
    # Test FactorDB connection on startup
    logging.info("Starting Prime Checker Service...")
    if test_factordb_connection():
        logging.info("FactorDB connectivity verified")
    else:
        logging.warning("FactorDB connectivity issues detected")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
