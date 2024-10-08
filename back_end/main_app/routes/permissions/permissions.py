import os

def is_authorized_admin_email(email):
    admin_emails_file = os.path.join(os.path.dirname(__file__), 'admin_emails.txt')
    try:
        with open(admin_emails_file, 'r') as file:
            authorized_emails = [line.strip() for line in file if line.strip()]
        return email in authorized_emails
    except FileNotFoundError:
        print(f"Warning: {admin_emails_file} not found. No admins can be created.")
        return False