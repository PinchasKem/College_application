import os
from flask_jwt_extended import  get_jwt
from werkzeug.exceptions import Forbidden
from functools import wraps


def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if not claims.get("is_admin", False):
                raise Forbidden("Admin access required")
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def is_authorized_admin_email(email):
    admin_emails_file = os.path.join(os.path.dirname(__file__), 'admin_emails.txt')
    try:
        with open(admin_emails_file, 'r') as file:
            authorized_emails = [line.strip() for line in file if line.strip()]
        return email in authorized_emails
    except FileNotFoundError:
        print(f"Warning: {admin_emails_file} not found. No admins can be created.")
        return False