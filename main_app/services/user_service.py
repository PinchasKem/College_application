from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import IntegrityError
from main_app.models.models import User
from main_app.extensions import db

class UserService:
    @staticmethod
    def create_user(username, email, class_cycle, password, is_student=False, is_staff_member=False, is_admin=False, is_guest=False):
        try:
            new_user = User(
                username=username,
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
    def create_access_token(user):
        additional_claims = {
            'is_admin': user.is_admin,
            'is_staff': user.is_staff_member,
            'is_student': user.is_student,
            'is_guest': user.is_guest
        }
        return create_access_token(identity=user.id, additional_claims=additional_claims)
    
    @staticmethod
    def create_refresh_token(user):
        return create_refresh_token(identity=user.id)

    @staticmethod
    def login(email, password):
        user = UserService.get_user_by_email_and_password(email, password)
        if user:
            access_token = UserService.create_access_token(user)
            refresh_token = UserService.create_refresh_token(user)
            return {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        return None

    @staticmethod
    def get_users_by_type(is_student=None, is_staff_member=None, is_admin=None, is_guest=None):
        query = User.query
        if is_student is not None:
            query = query.filter_by(is_student=is_student)
        if is_staff_member is not None:
            query = query.filter_by(is_staff_member=is_staff_member)
        if is_admin is not None:
            query = query.filter_by(is_admin=is_admin)
        if is_guest is not None:
            query = query.filter_by(is_guest=is_guest)
        return query.all()
    
    @staticmethod
    def get_users_by_class_cycle(class_cycle):
        return User.query.filter_by(class_cycle=class_cycle).all()
    
    @staticmethod
    def get_all_users():
        return User.query.all()
    
    @staticmethod
    def update_user(email, password, username=None, new_email=None, class_cycle=None, new_password=None, is_student=False, is_staff_member=False, is_admin=False, is_guest=False):
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if username:
                user.username = username
            if new_email:
                user.email = new_email
            if class_cycle is not None:
                user.class_cycle = class_cycle
            if new_password:
                user.set_password(new_password)
            
            if is_admin or is_guest or is_staff_member or is_student:
                user.is_student = is_student
                user.is_staff_member = is_staff_member
                user.is_admin = is_admin
                user.is_guest = is_guest
        
            try:
                db.session.commit()
                return user
            except IntegrityError:
                db.session.rollback()
                return None
        else:
            return None

    @staticmethod
    def is_admin(id):
        user = User.query.filter_by(id=id).first()
        return user.is_admin
    
    @staticmethod
    def is_staff_member(id):
        user = User.query.filter_by(id=id).first()
        return user.is_staff_member
    
    @staticmethod
    def is_guest(id):
        user = User.query.filter_by(id=id).first()
        return user.is_guest
    
    @staticmethod
    def is_student(id):
        user = User.query.filter_by(id=id).first()
        return user.is_student
    