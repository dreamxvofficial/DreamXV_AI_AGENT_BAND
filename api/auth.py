from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import json
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use bcrypt or safe hashlib fallback
try:
    import bcrypt
    use_bcrypt = True
except ImportError:
    import hashlib
    use_bcrypt = False

def hash_password(password: str) -> str:
    if use_bcrypt:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    else:
        # Fallback SHA256 with salt
        salt = "dreamxv_secure_salt_2087"
        db_pass = password + salt
        return hashlib.sha256(db_pass.encode('utf-8')).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    if use_bcrypt:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            # Fallback check if it was hashed with the fallback method
            pass
    
    salt = "dreamxv_secure_salt_2087"
    db_pass = password + salt
    expected = hashlib.sha256(db_pass.encode('utf-8')).hexdigest()
    return expected == hashed

def get_users_file_path() -> str:
    path = "data/users.json"
    if os.getenv("VERCEL") or not os.path.exists("data"):
        try:
            os.makedirs("data", exist_ok=True)
            # Test write
            test_file = "data/.write_test"
            with open(test_file, "w") as f:
                f.write("1")
            os.remove(test_file)
            return path
        except Exception:
            os.makedirs("/tmp/dreamxv", exist_ok=True)
            return "/tmp/dreamxv/users.json"
    return path

def load_users() -> dict:
    filepath = get_users_file_path()
    if not os.path.exists(filepath):
        # Create parent directories if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump({}, f)
        return {}
    
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users: dict):
    filepath = get_users_file_path()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(users, f, indent=4)

class SignupRequest(BaseModel):
    name: str
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class OnboardingRequest(BaseModel):
    username: str
    name: str
    creator_type: str
    favorite_genres: list
    dream_project: str

@app.post("/api/auth/signup")
@app.post("/signup")
async def signup(req: SignupRequest):
    try:
        users = load_users()
        username_lower = req.username.strip().lower()
        email_lower = req.email.strip().lower()
        print("Signup user:", email_lower)
        
        # Check duplicates
        for u_key, u_val in users.items():
            if u_key.lower() == username_lower:
                return {"success": False, "error": "Username already exists."}
            if u_val.get("email", "").lower() == email_lower:
                return {"success": False, "error": "Email already registered."}
        
        # Hash password
        hashed = hash_password(req.password)
        
        # Save user
        users[req.username] = {
            "name": req.name,
            "email": email_lower,
            "password_hash": hashed,
            "onboarded": False,
            "onboarding_answers": {}
        }
        save_users(users)
        
        return {
            "success": True,
            "user": {
                "name": req.name,
                "username": req.username,
                "email": email_lower,
                "onboarded": False
            }
        }
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": f"Signup failed: {str(e)}"}

@app.post("/api/auth/login")
@app.post("/login")
async def login(req: LoginRequest):
    try:
        users = load_users()
        query = req.username_or_email.strip().lower()
        print("Login attempt:", query)
        
        target_user = None
        target_username = None
        
        # Search by username or email
        for username, u_val in users.items():
            if username.lower() == query or u_val.get("email", "").lower() == query:
                target_user = u_val
                target_username = username
                break
                
        if not target_user:
            return {"success": False, "error": "Invalid username or email."}
            
        if not verify_password(req.password, target_user.get("password_hash", "")):
            return {"success": False, "error": "Invalid password."}
            
        return {
            "success": True,
            "user": {
                "name": target_user.get("name"),
                "username": target_username,
                "email": target_user.get("email"),
                "onboarded": target_user.get("onboarded", False),
                "onboarding_answers": target_user.get("onboarding_answers", {})
            }
        }
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": f"Login failed: {str(e)}"}

@app.post("/api/auth/onboarding")
@app.post("/onboarding")
async def save_onboarding(req: OnboardingRequest):
    try:
        users = load_users()
        if req.username not in users:
            return {"success": False, "error": "User not found."}
            
        users[req.username]["onboarded"] = True
        users[req.username]["onboarding_answers"] = {
            "name": req.name,
            "creator_type": req.creator_type,
            "favorite_genres": req.favorite_genres,
            "dream_project": req.dream_project
        }
        
        save_users(users)
        
        return {
            "success": True,
            "user": {
                "name": users[req.username].get("name"),
                "username": req.username,
                "email": users[req.username].get("email"),
                "onboarded": True,
                "onboarding_answers": users[req.username]["onboarding_answers"]
            }
        }
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": f"Failed to save onboarding: {str(e)}"}

@app.get("/api/auth/me")
@app.get("/me")
async def me(request: Request):
    # Session is handled on client-side, but returns status
    return {"success": True, "status": "authenticated"}

@app.post("/api/auth/logout")
@app.post("/logout")
async def logout():
    return {"success": True}
