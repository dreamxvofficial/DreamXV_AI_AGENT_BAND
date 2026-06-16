import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from api import auth

# Reset users
auth.save_users({})

# Test setup
print('=== AUTH VERIFICATION TESTS ===')
users_file = auth.get_users_file_path()
print(f'Users file path: {users_file}')
print(f'use_bcrypt: {auth.use_bcrypt}')

# Password hashing
pw = 'securepassword123'
hashed = auth.hash_password(pw)
print(f'Hashed (prefix): {hashed[:20]}...')

# Verify password
ok = auth.verify_password(pw, hashed)
print(f'verify correct pw: {ok}')
ok2 = auth.verify_password('wrongpassword', hashed)
print(f'verify wrong pw:   {ok2}')

# Save test user
auth.save_users({
    'dreamxv': {
        'username': 'dreamxv',
        'name': 'Sahir',
        'email': 'spotifysahir007@gmail.com',
        'password_hash': hashed,
        'onboarded': False,
        'onboarding_answers': {}
    }
})

# Load and verify
users = auth.load_users()
print(f'Users loaded: {list(users.keys())}')
u = users['dreamxv']
email_val = u['email']
print(f'Email: {email_val}')
final_verify = auth.verify_password('securepassword123', u['password_hash'])
print(f'Final verify password: {final_verify}')

# Login by username simulation
found_by_username = None
query_username = 'dreamxv'
for uname, uval in users.items():
    if uname.lower() == query_username.lower():
        found_by_username = uval
        break
print(f'Login by username found: {found_by_username is not None}')

# Login by email (mixed case) simulation
found_by_email = None
query_email = 'SpotifySahir007@GMAIL.COM'.lower()
for uname, uval in users.items():
    if uname.lower() == query_email or uval.get('email', '').lower() == query_email:
        found_by_email = uval
        break
print(f'Login by email found: {found_by_email is not None}')

print('=== ALL AUTH CHECKS DONE ===')
assert ok == True, 'verify_password should return True for correct password'
assert ok2 == False, 'verify_password should return False for wrong password'
assert found_by_username is not None, 'Username login should find user'
assert found_by_email is not None, 'Email login should find user'
assert final_verify == True, 'Final password verify should succeed'
print('=== ALL ASSERTIONS PASSED ===')
