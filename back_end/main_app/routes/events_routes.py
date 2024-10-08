from flask import jsonify, request, Blueprint, current_app
from main_app.services.events_service import EventService
from main_app.services.user_service import UserService
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

events_routes = Blueprint('events', __name__)

def get_event_service():
    return EventService(current_app.config['S3_BUCKET_NAME'])

@events_routes.route('/', methods=['GET'])
def get_all_events():
    try:
        event_service = get_event_service()
        events = event_service.get_all_events()
        return jsonify([event.to_dict() for event in events]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@events_routes.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    try:
        event_service = get_event_service()
        event = event_service.get_event(event_id)
        if not event:
            raise NotFound("Event not found")
        return jsonify(event.to_dict()), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@events_routes.route('/', methods=['POST'])
def create_event(user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin():
            raise Unauthorized("Only admins can create events")

        data = request.json
        if not data or 'title' not in data:
            raise BadRequest("Title is required")
        
        event_service = get_event_service()
        event = event_service.create_event(data['title'], data.get('description'))
        return jsonify(event.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@events_routes.route('/<int:event_id>', methods=['PUT'])
def update_event(event_id, user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin():
            raise Unauthorized("Only admins can create events")

        data = request.json
        if not data:
            raise BadRequest("No data provided")
        
        event_service = get_event_service()
        event = event_service.update_event(event_id, data.get('title'), data.get('description'))
        return jsonify(event.to_dict()), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@events_routes.route('/<int:event_id>', methods=['DELETE'])
def delete_event(event_id, user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin():
            raise Unauthorized("Only admins can create events")

        event_service = get_event_service()
        event_service.delete_event(event_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@events_routes.route('/<int:event_id>/images', methods=['POST'])
def add_image_to_event(event_id, user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin():
            raise Unauthorized("Only admins can create events")

        if 'file' not in request.files:
            raise BadRequest("No file part")
        file = request.files['file']
        if file.filename == '':
            raise BadRequest("No selected file")
        
        event_service = get_event_service()
        image = event_service.add_image_to_event(event_id, file.read(), file.filename)
        return jsonify(image.to_dict()), 201
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@events_routes.route('/<int:event_id>/images', methods=['GET'])
def get_event_images(event_id):
    try:
        event_service = get_event_service()
        images = event_service.get_event_images(event_id)
        return jsonify([image.to_dict() for image in images]), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@events_routes.route('/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id, user_id):
    try:
        is_admin = UserService.is_admin(user_id)
        if not is_admin():
            raise Unauthorized("Only admins can create events")
        
        event_service = get_event_service()
        event_service.delete_image(image_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    