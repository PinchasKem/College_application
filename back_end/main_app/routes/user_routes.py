from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from main_app.services.user_service import UserService
from werkzeug.exceptions import BadRequest, NotFound, Forbidden
from .permissions.permissions import  is_authorized_admin_email

user_routes = Blueprint('user', __name__)

@user_routes.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        if not data or 'firstname' not in data or 'lastname' not in data or 'email' not in data or 'password' not in data or 'user_type' not in data:
            raise BadRequest("firstname, lastname, email, password, and user_type are required")

        user_type = data['user_type']
        if user_type == 'is_admin':
            if not is_authorized_admin_email(data['email']):
                raise BadRequest("Unauthorized email for admin registration")
            
        if user_type not in ['is_guest', 'is_student', 'is_admin']:
            raise BadRequest("Invalid user_type. Must be 'guest' or 'student'")

        if user_type == 'is_student' and 'class_cycle' not in data:
            raise BadRequest("class_cycle is required for student registration")

        new_user = UserService.create_user(
            data['firstname'],
            data['lastname'],
            data['email'],
            data['class_cycle'] if user_type == 'student' else None,
            data['password'],
            is_student=(user_type == 'is_student'),
            is_staff_member=False,
            is_admin=(user_type == 'is_admin'),
            is_guest=(user_type == 'is_guest')
        )
        
        if new_user:
            return jsonify(new_user.to_dict()), 201
        else:
            return jsonify({"error": "User already exists"}), 409
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_routes.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data or 'email' not in data or 'password' not in data:
            raise BadRequest("Email and password are required")
        
        user = UserService.get_user_by_email_and_password(data['email'], data['password'])
        if user:
            access_token = create_access_token(identity=user.id, additional_claims={
                "is_admin": user.is_admin,
                "is_staff_member": user.is_staff_member,
                "is_student": user.is_student,
                "is_guest": user.is_guest
            })
            refresh_token = create_refresh_token(identity=user.id)
            return jsonify({
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_routes.route('/users', methods=['GET'])
def get_users():
    try:
        users = UserService.get_all_users()
        return jsonify([{
            'id': user.id,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'email': user.email,
            'role': 'admin' if user.is_admin else 'staff' if user.is_staff_member else 'student' if user.is_student else 'guest'
        } for user in users]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_routes.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = UserService.get_user_by_id(user_id)
        if user:
            return jsonify({
                'id': user.id,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'email': user.email,
                'role': 'admin' if user.is_admin else 'staff' if user.is_staff_member else 'student' if user.is_student else 'guest'
            }), 200
        else:
            raise NotFound("User not found")
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_routes.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            raise Forbidden("You can only update your own profile")
        
        data = request.json
        updated_user = UserService.update_user(user_id, data)
        if updated_user:
            return jsonify(updated_user.to_dict()), 200
        else:
            raise NotFound("User not found")
    except Forbidden as e:
        return jsonify({"error": str(e)}), 403
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_routes.route('/users/<int:user_id>/role', methods=['PUT'])
@jwt_required()
def update_user_role(user_id):
    try:
        current_user_id = get_jwt_identity()
        user = UserService.get_user_by_id(current_user_id)
        if not user.is_admin:
            raise Forbidden("Only the author or admin can edit this post")
        
        data = request.json
        valid_roles = ['is_admin', 'is_staff_member', 'is_student', 'is_guest']
        
        if not any(role in data for role in valid_roles):
            raise BadRequest("At least one valid role (is_admin, is_staff_member, is_student, or is_guest) is required")
        
        updated_user = UserService.update_user(user_id, data)
        if updated_user:
            return jsonify(updated_user.to_dict()), 200
        else:
            raise NotFound("User not found")
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_routes.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    user = UserService.get_user_by_id(current_user_id)
    new_access_token = create_access_token(identity=current_user_id, additional_claims={
        "is_admin": user.is_admin,
        "is_staff_member": user.is_staff_member,
        "is_student": user.is_student,
        "is_guest": user.is_guest
    })
    return jsonify(access_token=new_access_token), 200

