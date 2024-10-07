from flask import jsonify, request, Blueprint, current_app
from main_app.services.lesson_service import LessonService
from main_app.services.user_service import UserService
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

lessons_routes = Blueprint('lessons', __name__)

def get_lesson_service():
    return LessonService(current_app.config['S3_BUCKET_NAME'])

@lessons_routes.route('/', methods=['GET'])
def get_all_lessons():
    try:
        lesson_service = get_lesson_service()
        categories = lesson_service.get_all_categories()
        return jsonify([category.to_dict() for category in categories]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lessons_routes.route('/category/<int:category_id>', methods=['GET'])
def get_lessons_by_category(category_id):
    try:
        lesson_service = get_lesson_service()
        lessons = lesson_service.get_lessons_by_category(category_id)
        return jsonify([lesson.to_dict() for lesson in lessons]), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lessons_routes.route('/', methods=['POST'])
def create_lesson(user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin:
            raise Unauthorized("Only admins can create lessons")

        data = request.form
        if not data or 'title' not in data or 'is_audio' not in data or 'category_id' not in data:
            raise BadRequest("Title, is_audio, and category_id are required")

        if 'file' not in request.files:
            raise BadRequest("File is required")

        file = request.files['file']
        if file.filename == '':
            raise BadRequest("No selected file")

        lesson_service = get_lesson_service()
        lesson = lesson_service.create_lesson(
            title=data['title'],
            description=data.get('description'),
            is_audio=data['is_audio'].lower() == 'true',
            file_content=file.read(),
            file_name=file.filename,
            category_id=int(data['category_id'])
        )
        return jsonify(lesson.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lessons_routes.route('/<int:lesson_id>', methods=['PUT'])
def update_lesson(lesson_id, user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin:
            raise Unauthorized("Only admins can update lessons")

        data = request.form
        file = request.files.get('file')

        lesson_service = get_lesson_service()
        lesson = lesson_service.update_lesson(
            lesson_id=lesson_id,
            title=data.get('title'),
            description=data.get('description'),
            is_audio=data.get('is_audio'),
            file_content=file.read() if file else None,
            file_name=file.filename if file else None,
            category_id=data.get('category_id')
        )
        return jsonify(lesson.to_dict()), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lessons_routes.route('/<int:lesson_id>', methods=['DELETE'])
def delete_lesson(lesson_id, user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin:
            raise Unauthorized("Only admins can delete lessons")

        lesson_service = get_lesson_service()
        lesson_service.delete_lesson(lesson_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lessons_routes.route('/category', methods=['POST'])
def create_category(user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin:
            raise Unauthorized("Only admins can create categories")

        data = request.json
        if not data or 'name' not in data:
            raise BadRequest("Category name is required")

        lesson_service = get_lesson_service()
        category = lesson_service.create_category(data['name'])
        return jsonify(category.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lessons_routes.route('/category/<int:category_id>', methods=['DELETE'])
def delete_category(category_id, user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin:
            raise Unauthorized("Only admins can delete categories")

        lesson_service = get_lesson_service()
        lesson_service.delete_category(category_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    