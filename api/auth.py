from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from security.auth import create_access_token, get_current_user, require_roles
from services.auth_service import authenticate, create_user, get_all_users, get_user_by_id, update_user
from services.customer_service import create_customer
from services.email_service import send_registration_success_email

router=APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = None
    date_of_birth: str | None = None
    address: str | None = None

class LoginRequest(BaseModel):
    login: str
    password: str

class RoleUpdate(BaseModel):
    role: str
    active: bool | None = None

@router.post("/register")
def register(payload:RegisterRequest):
    try:
        customer=create_customer(payload.full_name, str(payload.email), payload.phone, payload.date_of_birth, payload.address)
        user=create_user(payload.username, str(payload.email), payload.password, payload.full_name, payload.phone, payload.date_of_birth, payload.address, "CUSTOMER", customer["id"])
        email_sent=send_registration_success_email(customer)
        return {"message":"Registration successful", "user":public_user(user), "customer":customer, "email_sent":email_sent, "access_token":create_access_token(user), "token_type":"bearer"}
    except Exception as exc:
        text=str(exc)
        if "UNIQUE" in text.upper() or "unique" in text.lower(): raise HTTPException(409, "Username or email already exists")
        raise HTTPException(400, text)

@router.post("/login")
def login(payload:LoginRequest):
    user=authenticate(payload.login, payload.password)
    if not user: raise HTTPException(401, "Invalid credentials or inactive account")
    return {"access_token":create_access_token(user), "token_type":"bearer", "user":public_user(user)}

@router.get("/me")
def me(user=Depends(get_current_user)): return public_user(user)

@router.get("/users")
def users(_:dict=Depends(require_roles("ADMIN"))): return get_all_users()

@router.patch("/users/{user_id}")
def update_user_route(user_id:int, payload:RoleUpdate, current=Depends(require_roles("ADMIN"))):
    target=get_user_by_id(user_id)
    if not target: raise HTTPException(404, "User not found")
    if target["id"] == current["id"] and payload.active is False: raise HTTPException(400, "Admin cannot disable the current account")
    try: updated=update_user(user_id, payload.role, payload.active)
    except ValueError as exc: raise HTTPException(400, str(exc))
    return public_user(updated)

def public_user(user):
    return {k:user.get(k) for k in ["id","username","email","full_name","phone","date_of_birth","address","role","active","customer_id","created_at"]}
