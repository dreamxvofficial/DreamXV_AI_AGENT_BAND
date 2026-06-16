from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import json
import hashlib  # Always import hashlib — used as bcrypt fallback
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.logger import logger
from backend.services.supabase_service import SupabaseService

db = SupabaseService()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project root is one directory above this file (api/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use bcrypt or safe hashlib fallback
try:
    import bcrypt
    use_bcrypt = True
    logger.info("bcrypt loaded successfully — using bcrypt for password hashing")
except ImportError:
    use_bcrypt = False
    logger.warning("bcrypt not available — falling back to SHA256 password hashing")


def hash_password(password: str) -> str:
    if use_bcrypt:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    else:
        # Fallback SHA256 with salt
        salt_str = "dreamxv_secure_salt_2087"
        db_pass = password + salt_str
        return hashlib.sha256(db_pass.encode('utf-8')).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a stored hash.
    Tries bcrypt first (if available), then SHA256 fallback.
    """
    if use_bcrypt:
        try:
            result = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            logger.info(f"bcrypt.checkpw result: {result}")
            return result
        except Exception as bcrypt_err:
            logger.warning(f"bcrypt.checkpw raised exception: {bcrypt_err} — trying SHA256 fallback")

    # SHA256 fallback — always reachable because hashlib is imported at module level
    salt_str = "dreamxv_secure_salt_2087"
    db_pass = password + salt_str
    expected = hashlib.sha256(db_pass.encode('utf-8')).hexdigest()
    result = expected == hashed
    logger.info(f"SHA256 fallback verify result: {result}")
    return result


def get_users_file_path() -> str:
    """
    Return the absolute path to users.json.
    Uses /tmp/dreamxv on Vercel/Lambda; otherwise uses <project_root>/data/users.json.
    Never depends on the current working directory.
    """
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_dir = "/tmp/dreamxv"
        try:
            os.makedirs(tmp_dir, exist_ok=True)
            return os.path.join(tmp_dir, "users.json")
        except Exception:
            pass  # Fall through to local path

    # Absolute local path relative to project root
    local_data_dir = os.path.join(_PROJECT_ROOT, "data")
    local_path = os.path.join(local_data_dir, "users.json")
    try:
        os.makedirs(local_data_dir, exist_ok=True)
    except Exception:
        pass
    return local_path


def load_users() -> dict:
    filepath = get_users_file_path()
    logger.info(f"Loading users from: {filepath}")
    if not os.path.exists(filepath):
        logger.info("users.json not found — creating empty file")
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        except Exception:
            pass
        try:
            with open(filepath, "w") as f:
                json.dump({}, f)
        except Exception as e:
            logger.error(f"Could not create users.json: {e}")
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} user record(s)")
            return data
    except Exception as e:
        logger.error(f"Failed to load users.json: {e}")
        return {}


def save_users(users: dict):
    filepath = get_users_file_path()
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    except Exception:
        pass
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)
    logger.info(f"Saved {len(users)} user record(s) to {filepath}")


# ─── Pydantic Models ──────────────────────────────────────────────────────

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


# ─── Routes ───────────────────────────────────────────────────────────────

@app.post("/api/auth/signup")
@app.post("/signup")
async def signup(req: SignupRequest):
    try:
        username_lower = req.username.strip().lower()
        email_lower = req.email.strip().lower()
        logger.info(f"Signup attempt — username: {username_lower}, email: {email_lower}")

        # Check for duplicate username (case-insensitive)
        user_by_username = db.get_user_by_username_or_email(username_lower)
        if user_by_username and user_by_username.get("username", "").lower() == username_lower:
            logger.info(f"Signup rejected: username '{username_lower}' already exists")
            return {"success": False, "error": "Username already exists."}

        # Check for duplicate email (case-insensitive)
        user_by_email = db.get_user_by_username_or_email(email_lower)
        if user_by_email and user_by_email.get("email", "").lower() == email_lower:
            logger.info(f"Signup rejected: email '{email_lower}' already registered")
            return {"success": False, "error": "Email already registered."}

        # Hash password
        hashed = hash_password(req.password)

        # Create user in Supabase
        new_user = db.create_user(
            username=req.username,
            name=req.name,
            email=email_lower,
            password_hash=hashed
        )
        if not new_user:
            return {"success": False, "error": "Failed to create user record in Supabase."}

        logger.info(f"Signup successful for '{req.username}' / '{email_lower}'")

        return {
            "success": True,
            "message": "Account created successfully",
            "user": {
                "id": new_user.get("id"),
                "name": req.name,
                "username": req.username,
                "email": email_lower,
                "onboarded": False
            }
        }
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Signup exception: {e}")
        return {"success": False, "error": f"Signup failed: {str(e)}"}


@app.post("/api/auth/login")
@app.post("/login")
async def login(req: LoginRequest):
    try:
        identifier = req.username_or_email.strip()
        logger.info(f"Login attempt: {identifier}")

        target_user = db.get_user_by_username_or_email(identifier)

        if not target_user:
            logger.warning(f"Login failed: no user found for identifier '{identifier}'")
            return {"success": False, "error": "User not found. Please check your username or email."}

        target_username = target_user.get("username")
        logger.info(f"User found: {target_username} (email={target_user.get('email')})")

        stored_hash = target_user.get("password_hash", "")
        logger.info(f"Stored hash prefix: '{stored_hash[:10]}...' (len={len(stored_hash)})")

        if not verify_password(req.password, stored_hash):
            logger.warning(f"Login failed: incorrect password for user '{target_username}'")
            return {"success": False, "error": "Incorrect password."}

        logger.info(f"Login successful for '{target_username}'")
        return {
            "success": True,
            "user": {
                "id": target_user.get("id"),
                "name": target_user.get("full_name") or target_user.get("name"),
                "username": target_username,
                "email": target_user.get("email"),
                "onboarded": target_user.get("onboarded", False),
                "onboarding_answers": target_user.get("onboarding_answers", {})
            }
        }
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Login exception: {e}")
        return {"success": False, "error": f"Login failed: {str(e)}"}


@app.post("/api/auth/onboarding")
@app.post("/onboarding")
async def save_onboarding(req: OnboardingRequest):
    try:
        answers = {
            "name": req.name,
            "creator_type": req.creator_type,
            "favorite_genres": req.favorite_genres,
            "dream_project": req.dream_project
        }
        updated_user = db.update_user_onboarding(
            username=req.username,
            onboarded=True,
            onboarding_answers=answers
        )
        if not updated_user:
            return {"success": False, "error": "User not found or failed to update onboarding answers."}

        return {
            "success": True,
            "user": {
                "id": updated_user.get("id"),
                "name": updated_user.get("full_name") or updated_user.get("name"),
                "username": req.username,
                "email": updated_user.get("email"),
                "onboarded": True,
                "onboarding_answers": updated_user.get("onboarding_answers")
            }
        }
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": f"Failed to save onboarding: {str(e)}"}


@app.get("/api/auth/me")
@app.get("/me")
async def me(request: Request):
    # Session is handled on client-side
    return {"success": True, "status": "authenticated"}


@app.post("/api/auth/logout")
@app.post("/logout")
async def logout():
    return {"success": True}
