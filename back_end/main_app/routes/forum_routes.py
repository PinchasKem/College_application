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
@jwt_required()
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

        if current_user_id != post.author_id and not current_user.is_admin:
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
        forum_service = get_forum_service()
        post = forum_service.get_post_by_id(post_id)
        
        if not post:
            raise NotFound("Post not found")

        current_user_id = get_jwt_identity()
        current_user = User.query.filter_by(id=current_user_id).first()

        if current_user_id != post.author_id and not current_user.is_admin:
            raise Forbidden("Only the author or admin can delete this post")

        forum_service.delete_post(post_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts/<int:post_id>/replies', methods=['GET'])
def get_replies_by_post(post_id):
    try:
        forum_service = get_forum_service()
        post = forum_service.get_post_by_id(post_id)
        if not post:
            raise NotFound("Post not found")
        replies = forum_service.get_replies_by_post(post_id)

        return jsonify([reply.to_dict() for reply in replies]), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts/<int:post_id>/replies', methods=['POST'], endpoint='create_reply')
@jwt_required()
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

@forum_routes.route('/replies/<int:reply_id>', methods=['PUT'])
@jwt_required()
def update_reply(reply_id):
    try:
        data = request.json
        if not data:
            raise BadRequest("No data provided")
        
        forum_service = get_forum_service()
        reply = forum_service.get_reply_by_id(reply_id)
        
        if not reply:
            raise NotFound("Reply not found")

        current_user_id = get_jwt_identity()
        current_user = User.query.filter_by(id=current_user_id).first()

        if current_user_id != reply.author_id and not current_user.is_admin:
            raise Forbidden("Only the author or admin can edit this reply")
        
        updated_reply = forum_service.update_reply(reply_id, data.get('content'))
        return jsonify(updated_reply.to_dict()), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/replies/<int:reply_id>', methods=['DELETE'], endpoint='delete_reply')
@jwt_required()
def delete_reply(reply_id):
    try:        
        forum_service = get_forum_service()
        reply = forum_service.get_reply_by_id(reply_id)
        
        if not reply:
            raise NotFound("Reply not found")

        current_user_id = get_jwt_identity()
        current_user = User.query.filter_by(id=current_user_id).first()

        if current_user_id != reply.author_id and not current_user.is_admin:
            raise Forbidden("Only the author or admin can delete this reply")

        forum_service.delete_reply(reply_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/clusters', methods=['POST'], endpoint='create_cluster')
@jwt_required()
def create_cluster():
    try:   
        data = request.json
        if not data or 'name' not in data:
            raise BadRequest("Cluster name is required")
        
        current_user_id = get_jwt_identity()
        current_user = User.query.filter_by(id=current_user_id).first()

        if not current_user_id:
            raise Forbidden("The user is not registered in the system")

        forum_service = get_forum_service()
        cluster = forum_service.create_cluster(data['name'], current_user_id, data.get('description'))
        return jsonify(cluster.to_dict()), 201
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/clusters/<int:cluster_id>', methods=['PUT'])
@jwt_required()
def update_cluster(cluster_id):
    try:
        data = request.json
        if not data:
            raise BadRequest("No data provided")
        
        forum_service = get_forum_service()
        cluster = forum_service.get_cluster_by_id(cluster_id)
        
        if not cluster:
            raise NotFound("Cluster not found")

        current_user_id = get_jwt_identity()
        current_user = User.query.filter_by(id=current_user_id).first()

        if current_user_id != cluster.author_id and not current_user.is_admin:
            raise Forbidden("Only the author or admin can edit this cluster")
        
        updated_cluster = forum_service.update_cluster(cluster_id, data.get('name'), data.get('description'))
        return jsonify(updated_cluster.to_dict()), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/clusters/<int:cluster_id>', methods=['DELETE'])
@jwt_required()
def delete_cluster(cluster_id):
    try:        
        forum_service = get_forum_service()
        cluster = forum_service.get_cluster_by_id(cluster_id)
        
        if not cluster:
            raise NotFound("Cluster not found")

        current_user_id = get_jwt_identity()
        current_user = User.query.filter_by(id=current_user_id).first()

        if current_user_id != cluster.author_id and not current_user.is_admin:
            raise Forbidden("Only the author or admin can delete this cluster")

        forum_service.delete_cluster(cluster_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
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


@forum_routes.route('/posts/<int:post_id>/attachments', methods=['POST'])
def add_attachment(post_id):
    try:
        if 'file' not in request.files:
            raise BadRequest("No file part")
        file = request.files['file']
        if file.filename == '':
            raise BadRequest("No selected file")
        
        forum_service = get_forum_service()
        attachment = forum_service.add_attachment_to_post(
            post_id, 
            file.filename, 
            file.read(), 
            file_type=file.content_type  
        )
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
    