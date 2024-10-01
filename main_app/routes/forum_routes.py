from flask import jsonify, request, Blueprint, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from main_app.models.models import User, ForumPost
from main_app.services.forum_service import ForumService
from main_app.services.user_service import UserService
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized, Forbidden



forum_routes = Blueprint('forum', __name__)

def get_forum_service():
    return ForumService(current_app.config['S3_BUCKET_NAME'])

@forum_routes.route('/posts', methods=['GET'])
def get_all_posts():
    try:
        forum_service = get_forum_service()
        posts = forum_service.get_all_posts()
        return jsonify([post.to_dict() for post in posts]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts', methods=['POST'])
@jwt_required
def create_post():
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            raise BadRequest("Title and content are required")
        
        current_user = get_jwt_identity()
        
        existing_post = ForumPost.query.filter_by(title=data['title']).first()
        if existing_post:
            raise ValueError("כותרת זו כבר קיימת. אנא בחר כותרת אחרת.")

        forum_service = get_forum_service()
        post = forum_service.create_post(data['title'], data['content'], current_user, data.get('cluster_id'))
        return jsonify(post.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    try:
        data = request.json
        if not data:
            raise BadRequest("No data provided")
        
        forum_service = get_forum_service()
        post = forum_service.get_post_by_id(post_id)
        
        if not post:
            raise NotFound("Post not found")

        current_user_id = get_jwt_identity()
        current_user = User.query.filter_by(id=current_user_id).first()

        if current_user_id != post.author_id or not current_user.is_admin:
            raise Forbidden("Only the author or admin can edit this post")
        
        updated_post = forum_service.update_post(post_id, data.get('title'), data.get('content'))
        return jsonify(updated_post.to_dict()), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    try:
        data = request.json
        if not data:
            raise BadRequest("No data provided")
        
        forum_service = get_forum_service()
        post = forum_service.get_post_by_id(post_id)
        
        if not post:
            raise NotFound("Post not found")

        current_user_id = get_jwt_identity()
        current_user = User.query.filter_by(id=current_user_id).first()

        if current_user_id != post.author_id or not current_user.is_admin:
            raise Forbidden("Only the author or admin can edit this post")

        forum_service.delete_post(post_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts/<int:post_id>/replies', methods=['POST'], endpoint='create_reply')
@jwt_required
def create_reply(post_id):
    try:
        data = request.json
        if not data or 'content' not in data:
            raise BadRequest("Content are required")
        
        current_user_id = get_jwt_identity()

        forum_service = get_forum_service()
        reply = forum_service.create_reply(data['content'], current_user_id, post_id)
        return jsonify(reply.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/clusters', methods=['POST'], endpoint='create_cluster')
@jwt_required
def create_cluster():
    try:   
        data = request.json
        if not data or 'name' not in data:
            raise BadRequest("Cluster name is required")
        
        current_user = get_jwt_identity()

        forum_service = get_forum_service()
        cluster = forum_service.create_cluster(data['name'], data.get('description'), current_user)
        return jsonify(cluster.to_dict()), 201
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/clusters', methods=['GET'])
def get_all_clusters():
    try:
        forum_service = get_forum_service()
        clusters = forum_service.get_all_clusters()
        return jsonify([cluster.to_dict() for cluster in clusters]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/search', methods=['GET'])
def search_forum():
    try:
        query = request.args.get('q', '')
        forum_service = get_forum_service()
        results = forum_service.search(query)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts/<int:post_id>/attachments', methods=['POST'])
def add_attachment(post_id):
    try:
        if 'file' not in request.files:
            raise BadRequest("No file part")
        file = request.files['file']
        if file.filename == '':
            raise BadRequest("No selected file")
        
        forum_service = get_forum_service()
        attachment = forum_service.add_attachment_to_post(post_id, file.filename, file.read(), file.content_type)
        return jsonify(attachment.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/attachments/<int:attachment_id>', methods=['DELETE'])
def delete_attachment(attachment_id):
    try:
        user_id = request.headers.get('User-ID') 
        if not UserService.is_admin(user_id):
            raise Unauthorized("Only admins can delete attachments")

        forum_service = get_forum_service()
        forum_service.delete_attachment(attachment_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    