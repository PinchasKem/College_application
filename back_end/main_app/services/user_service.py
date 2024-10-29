from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import IntegrityError
from main_app.models.models import User
from main_app.extensions import db

class UserService:
    @staticmethod
    def create_user(firstname, lastname, email, class_cycle, password, is_student=False, is_staff_member=False, is_admin=False, is_guest=False):
        try:
            new_user = User(
                firstname=firstname,
                lastname=lastname,
                email=email,
                class_cycle=class_cycle,
                password=password,
                is_student=is_student,
                is_staff_member=is_staff_member,
                is_admin=is_admin,
                is_guest=is_guest
            )
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except IntegrityError:
            db.session.rollback()
            return None
    
    @staticmethod
    def get_user_by_email_and_password(email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None
    
    @staticmethod
    def get_all_users():
        return User.query.all()
    
    @staticmethod
    def get_user_by_id(id):
        return User.query.filter_by(id=id).first()
    
    @staticmethod
    def update_user(user_id, data):
        user = User.query.get(user_id)
        if not user:
            return None
        if 'firstname' in data:
            user.firstname = data['firstname']
        if 'lastname' in data:
            user.lastname = data['lastname']
        if 'new_email' in data:
            user.email = data['new_email']
        if 'class_cycle' in data:
            user.class_cycle = data['class_cycle']
        if 'new_password' in data:
            user.set_password(data['new_password'])
        
        user.is_student = data.get('is_student', user.is_student)
        user.is_staff_member = data.get('is_staff_member', user.is_staff_member)
        user.is_admin = data.get('is_admin', user.is_admin)
        user.is_guest = data.get('is_guest', user.is_guest)

        try:
            db.session.commit()
            return user
        except IntegrityError:
            db.session.rollback()
            return None
     