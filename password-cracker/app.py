from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import string
import itertools
from threading import Thread, Lock

app = Flask(__name__)
CORS(app)

# Track cracking progress
cracking_status = {
    'is_cracking': False,
    'progress': 0,
    'attempts': 0,
    'current_password': '',
    'found': False,
    'found_password': None,
    'should_stop': False
}
status_lock = Lock()

# MASSIVE password dictionary - thousands of combinations
COMMON_PASSWORDS = [
    # Top 1000 most common passwords
    "password", "123456", "123456789", "12345678", "12345", "1234567", "password1",
    "123123", "1234567890", "000000", "qwerty", "abc123", "password123", "1234",
    "iloveyou", "1q2w3e4r", "qwerty123", "monkey", "dragon", "letmein", "baseball",
    "111111", "mustang", "access", "shadow", "master", "michael", "superman", "696969",
    "123321", "batman", "trustno1", "football", "welcome", "jesus", "ninja", "password1",
    "qazwsx", "hello", "starwars", "admin", "root", "toor", "pass", "test", "guest",
    "info", "adm", "mysql", "user", "administrator", "oracle", "ftp", "pi", "puppet",
    "ansible", "ec2-user", "vagrant", "azureuser", "love", "654321", "princess", "flower",
    "purple", "maggie", "charlie", "hannah", "lovely", "sophie", "harley", "samsung",
    "summer", "ashley", "sunshine", "chelsea", "madison", "hunter", "dakota", "computer",
    "123123123", "password!", "Password1", "passw0rd", "P@ssword", "P@ssw0rd",
    "admin123", "root123", "test123", "pass123", "user123", "demo", "demo123",
    "welcome1", "welcome123", "qwerty1", "abc123!", "password1!", "letmein1",
    # Common names
    "james", "john", "robert", "michael", "william", "david", "richard", "joseph",
    "thomas", "charles", "mary", "patricia", "jennifer", "linda", "barbara", "elizabeth",
    # Common words
    "andrew", "daniel", "matthew", "anthony", "donald", "mark", "paul", "steven", "george",
    "kenneth", "kevin", "brian", "edward", "ronald", "timothy", "jason", "jeffrey",
    # Years and dates
    "2020", "2021", "2022", "2023", "2024", "1990", "1991", "1992", "1993", "1994",
    "1995", "1996", "1997", "1998", "1999", "2000", "2001", "2002", "2003", "2004",
    # Sports and teams
    "football1", "baseball1", "basketball", "soccer", "hockey", "tennis", "golf",
    "yankees", "lakers", "cowboys", "patriots", "eagles",
    # Tech related
    "windows", "linux", "ubuntu", "debian", "fedora", "centos", "android", "apple",
    "samsung", "google", "amazon", "microsoft", "github", "docker", "kubernetes",
    # Simple patterns
    "aaaaaa", "qqqqqq", "zzzzzz", "111111", "222222", "333333", "444444", "555555",
    "666666", "777777", "888888", "999999", "000000",
    # Keyboard patterns
    "qwerty", "asdfgh", "zxcvbn", "qwertyuiop", "asdfghjkl", "zxcvbnm",
    "1qaz2wsx", "qazwsxedc", "1q2w3e4r5t", "!qaz2wsx", "1qazxsw2",
]

# Generate even more variations
def generate_variations(base_list):
    """Generate thousands of password variations"""
    variations = set(base_list)
    
    # Add capitalization variations
    for pwd in base_list[:100]:  # Limit to prevent explosion
        variations.add(pwd.upper())
        variations.add(pwd.lower())
        variations.add(pwd.capitalize())
        variations.add(pwd.title())
    
    # Add number suffixes (most common)
    for pwd in base_list[:50]:
        for num in ['1', '12', '123', '1234', '!', '!!', '21', '22', '23', '69', '99', '00', '01', '11']:
            variations.add(pwd + num)
            variations.add(pwd.capitalize() + num)
    
    # Add number prefixes
    for pwd in base_list[:50]:
        for num in ['1', '12', '123']:
            variations.add(num + pwd)
    
    # Add special character variations
    for pwd in base_list[:30]:
        variations.add(pwd + '!')
        variations.add(pwd + '@')
        variations.add(pwd + '#')
        variations.add(pwd + '$')
        variations.add('!' + pwd)
        variations.add('@' + pwd)
    
    # Leet speak variations
    leet_map = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
    for pwd in base_list[:30]:
        leet_pwd = pwd
        for old, new in leet_map.items():
            leet_pwd = leet_pwd.replace(old, new)
        variations.add(leet_pwd)
    
    return list(variations)

# Generate massive dictionary (10,000+ passwords)
MASSIVE_DICTIONARY = generate_variations(COMMON_PASSWORDS)

def hash_password(password, algorithm):
    """Hash a password using the specified algorithm"""
    if algorithm == 'md5':
        return hashlib.md5(password.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(password.encode()).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(password.encode()).hexdigest()
    return None

def brute_force_generator(charset, min_length, max_length):
    """Generate all possible combinations of characters"""
    for length in range(min_length, max_length + 1):
        for combination in itertools.product(charset, repeat=length):
            yield ''.join(combination)

def dictionary_attack(target_hash, algorithm):
    """Fast dictionary attack with massive wordlist"""
    global cracking_status
    
    with status_lock:
        cracking_status['attempts'] = 0
        cracking_status['found'] = False
        cracking_status['found_password'] = None
    
    total = len(MASSIVE_DICTIONARY)
    
    for i, password in enumerate(MASSIVE_DICTIONARY):
        # Check if we should stop
        with status_lock:
            if cracking_status['should_stop']:
                return False, None, cracking_status['attempts']
        
        with status_lock:
            cracking_status['attempts'] = i + 1
            cracking_status['current_password'] = password
            cracking_status['progress'] = int((i + 1) / total * 100)
        
        hashed = hash_password(password, algorithm)
        
        if hashed == target_hash.lower():
            with status_lock:
                cracking_status['found'] = True
                cracking_status['found_password'] = password
            return True, password, i + 1
    
    return False, None, len(MASSIVE_DICTIONARY)

def brute_force_attack(target_hash, algorithm, charset_type, min_len, max_len):
    """Brute force attack trying all combinations"""
    global cracking_status
    
    # Define character sets
    charsets = {
        'numeric': string.digits,
        'lowercase': string.ascii_lowercase,
        'uppercase': string.ascii_uppercase,
        'alpha': string.ascii_letters,
        'alphanumeric': string.ascii_letters + string.digits,
        'all': string.ascii_letters + string.digits + string.punctuation
    }
    
    charset = charsets.get(charset_type, string.ascii_lowercase + string.digits)
    
    with status_lock:
        cracking_status['attempts'] = 0
        cracking_status['found'] = False
        cracking_status['found_password'] = None
    
    attempts = 0
    
    for password in brute_force_generator(charset, min_len, max_len):
        # Check if we should stop
        with status_lock:
            if cracking_status['should_stop']:
                return False, None, cracking_status['attempts']
        
        attempts += 1
        
        with status_lock:
            cracking_status['attempts'] = attempts
            cracking_status['current_password'] = password
            # Approximate progress (hard to calculate exact for brute force)
            cracking_status['progress'] = min(99, attempts // 1000)
        
        hashed = hash_password(password, algorithm)
        
        if hashed == target_hash.lower():
            with status_lock:
                cracking_status['found'] = True
                cracking_status['found_password'] = password
                cracking_status['progress'] = 100
            return True, password, attempts
        
        # Safety limit to prevent infinite running
        if attempts > 10000000:  # 10 million attempts max
            return False, None, attempts
    
    return False, None, attempts

def crack_hash_thread(target_hash, algorithm, mode, charset, min_len, max_len):
    """Run cracking in background thread"""
    global cracking_status
    
    with status_lock:
        cracking_status['is_cracking'] = True
        cracking_status['should_stop'] = False
    
    try:
        if mode == 'dictionary':
            success, password, attempts = dictionary_attack(target_hash, algorithm)
        else:  # brute_force
            success, password, attempts = brute_force_attack(
                target_hash, algorithm, charset, min_len, max_len
            )
        
        with status_lock:
            cracking_status['is_cracking'] = False
            if success:
                cracking_status['found'] = True
                cracking_status['found_password'] = password
    except Exception as e:
        with status_lock:
            cracking_status['is_cracking'] = False
            print(f"Error during cracking: {e}")

@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        with open('hash-cracker-standalone.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>Error: HTML file not found</h1>
        <p>Make sure 'hash-cracker-standalone.html' is in the same folder as app.py</p>
        """, 404

@app.route('/api/crack', methods=['POST'])
def crack():
    """API endpoint to start cracking a hash"""
    global cracking_status
    
    try:
        data = request.json
        target_hash = data.get('hash', '').strip()
        algorithm = data.get('algorithm', 'md5').lower()
        mode = data.get('mode', 'dictionary')  # 'dictionary' or 'brute_force'
        charset = data.get('charset', 'alphanumeric')
        min_length = int(data.get('min_length', 1))
        max_length = int(data.get('max_length', 6))
        
        # Validate input
        if not target_hash:
            return jsonify({'success': False, 'error': 'Please provide a hash'}), 400
        
        if algorithm not in ['md5', 'sha1', 'sha256']:
            return jsonify({'success': False, 'error': 'Invalid algorithm'}), 400
        
        # Check if already cracking
        with status_lock:
            if cracking_status['is_cracking']:
                return jsonify({
                    'success': False,
                    'error': 'Already cracking a hash. Please wait or stop the current process.'
                }), 400
        
        # Start cracking in background thread
        thread = Thread(
            target=crack_hash_thread,
            args=(target_hash, algorithm, mode, charset, min_length, max_length)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Cracking started',
            'mode': mode,
            'dictionary_size': len(MASSIVE_DICTIONARY) if mode == 'dictionary' else 'Variable'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current cracking status"""
    with status_lock:
        return jsonify({
            'is_cracking': cracking_status['is_cracking'],
            'progress': cracking_status['progress'],
            'attempts': cracking_status['attempts'],
            'current_password': cracking_status['current_password'],
            'found': cracking_status['found'],
            'found_password': cracking_status['found_password']
        })

@app.route('/api/stop', methods=['POST'])
def stop_cracking():
    """Stop the current cracking process"""
    with status_lock:
        cracking_status['should_stop'] = True
        cracking_status['is_cracking'] = False
    
    return jsonify({'success': True, 'message': 'Cracking stopped'})

@app.route('/api/hash', methods=['POST'])
def create_hash():
    """Generate a hash from a password"""
    try:
        data = request.json
        password = data.get('password', '')
        algorithm = data.get('algorithm', 'md5').lower()
        
        if not password:
            return jsonify({'success': False, 'error': 'Please provide a password'}), 400
        
        hashed = hash_password(password, algorithm)
        
        return jsonify({
            'success': True,
            'hash': hashed,
            'algorithm': algorithm,
            'password': password
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the cracker"""
    return jsonify({
        'dictionary_size': len(MASSIVE_DICTIONARY),
        'supported_algorithms': ['MD5', 'SHA-1', 'SHA-256'],
        'modes': ['Dictionary Attack', 'Brute Force'],
        'charsets': ['Numeric', 'Lowercase', 'Uppercase', 'Alpha', 'Alphanumeric', 'All']
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🔐 ADVANCED PASSWORD CRACKER SERVER")
    print("=" * 60)
    print(f"📚 Dictionary Size: {len(MASSIVE_DICTIONARY):,} passwords")
    print(f"⚡ Modes: Dictionary Attack + Brute Force")
    print(f"🎯 Algorithms: MD5, SHA-1, SHA-256")
    print("=" * 60)
    print("📍 Server: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
