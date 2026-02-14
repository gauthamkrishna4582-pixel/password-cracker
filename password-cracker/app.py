from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for API requests

# MASSIVE password dictionary - 200+ common passwords
COMMON_PASSWORDS = [
    # Top most common
    "password", "123456", "123456789", "12345678", "12345", "1234567",
    "password1", "123123", "1234567890", "000000", "qwerty", "abc123",
    "password123", "1234", "iloveyou", "1q2w3e4r", "qwerty123",
    "monkey", "dragon", "letmein", "baseball", "111111", "mustang",
    "access", "shadow", "master", "michael", "superman", "696969",
    "123321", "batman", "trustno1", "football", "welcome", "jesus",
    "ninja", "qazwsx", "hello", "starwars", "princess", "solo",
    "admin", "root", "toor", "pass", "test", "guest", "info", "adm",
    "mysql", "user", "administrator", "oracle", "ftp", "pi", "puppet",
    
    # More numbers
    "0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888", "9999",
    "00000", "11111", "22222", "33333", "44444", "55555", "66666", "77777", "88888", "99999",
    "000000", "111111", "222222", "333333", "444444", "555555", "666666", "777777", "888888", "999999",
    "1212", "1313", "1414", "1515", "1616", "1717", "1818", "1919", "2020", "2021", "2022", "2023", "2024",
    
    # Common words
    "love", "lover", "loving", "loveyou", "loveme", "baby", "honey", "angel", "sunshine",
    "charlie", "ashley", "bailey", "tiger", "buster", "computer", "internet", "laptop",
    "apple", "google", "facebook", "twitter", "instagram", "amazon", "netflix",
    
    # Keyboard patterns
    "qwertyuiop", "asdfgh", "asdfghjkl", "zxcvbn", "zxcvbnm",
    "1qaz2wsx", "qazwsx", "qweasd", "qweasdzxc", "zaq1zaq1",
    
    # Names
    "john", "david", "michael", "james", "robert", "william", "mary", "jennifer",
    "linda", "patricia", "susan", "jessica", "ashley", "emily", "sarah", "amanda",
    "daniel", "matthew", "andrew", "joseph", "christopher", "ryan", "nicole",
    
    # Years
    "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015",
    "2000", "1999", "1998", "1997", "1996", "1995", "1994", "1993", "1992", "1991", "1990",
    
    # Simple
    "abc", "abc123", "123abc", "admin123", "root123", "pass123", "test123",
    "password1", "password12", "password123", "admin1", "admin12",
]

def hash_password(password, algorithm):
    """Hash a password using the specified algorithm"""
    if algorithm == 'md5':
        return hashlib.md5(password.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(password.encode()).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(password.encode()).hexdigest()
    return None

def crack_hash(target_hash, algorithm):
    """
    Attempt to crack a hash using dictionary attack
    Returns: (success, password, attempts)
    """
    attempts = 0
    
    # Try common passwords
    for password in COMMON_PASSWORDS:
        attempts += 1
        hashed = hash_password(password, algorithm)
        
        if hashed == target_hash.lower():
            return True, password, attempts
        
        # Also try common variations
        variations = [
            password.upper(),
            password.capitalize(),
            password + "123",
            password + "!",
            password + "1",
            "1" + password,
            password + "@",
            password + "#",
            password + "$",
        ]
        
        for variation in variations:
            attempts += 1
            hashed = hash_password(variation, algorithm)
            if hashed == target_hash.lower():
                return True, variation, attempts
    
    return False, None, attempts

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
        <p>Your folder should contain:</p>
        <ul>
            <li>app.py</li>
            <li>hash-cracker-standalone.html</li>
        </ul>
        """, 404

@app.route('/api/crack', methods=['POST'])
def crack():
    """API endpoint to crack a hash"""
    try:
        data = request.json
        target_hash = data.get('hash', '').strip()
        algorithm = data.get('algorithm', 'md5').lower()
        
        # Validate input
        if not target_hash:
            return jsonify({
                'success': False,
                'error': 'Please provide a hash to crack'
            }), 400
        
        if algorithm not in ['md5', 'sha1', 'sha256']:
            return jsonify({
                'success': False,
                'error': 'Invalid algorithm. Choose md5, sha1, or sha256'
            }), 400
        
        # Simulate some processing time for demo purposes
        time.sleep(0.5)
        
        # Attempt to crack the hash
        success, password, attempts = crack_hash(target_hash, algorithm)
        
        if success:
            return jsonify({
                'success': True,
                'password': password,
                'attempts': attempts,
                'message': f'Password cracked successfully in {attempts} attempts!'
            })
        else:
            return jsonify({
                'success': False,
                'attempts': attempts,
                'message': f'Password not found after {attempts} attempts. Try a more common password or expand the dictionary.'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hash', methods=['POST'])
def create_hash():
    """API endpoint to create a hash from a password (for testing)"""
    try:
        data = request.json
        password = data.get('password', '')
        algorithm = data.get('algorithm', 'md5').lower()
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'Please provide a password'
            }), 400
        
        hashed = hash_password(password, algorithm)
        
        return jsonify({
            'success': True,
            'hash': hashed,
            'algorithm': algorithm,
            'password': password
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Get port from environment variable (for hosting platforms like Render, Heroku)
    port = int(os.environ.get('PORT', 5000))
    # Set debug=False for production
    app.run(debug=False, host='0.0.0.0', port=port)
