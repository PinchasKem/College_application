from flask import jsonify, request, Blueprint, current_app
from main_app.services.forum_service import ForumService
from main_app.services.user_service import UserService
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

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
def create_post():
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data or 'author_id' not in data:
            raise BadRequest("Title, content, and author_id are required")
        
        forum_service = get_forum_service()
        post = forum_service.create_post(data['title'], data['content'], data['author_id'], data.get('cluster_id'))
        return jsonify(post.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    try:
        data = request.json
        if not data:
            raise BadRequest("No data provided")
        
        forum_service = get_forum_service()
        post = forum_service.get_post(post_id)
        if not post:
            raise NotFound("Post not found")
        
        if post.author_id != data.get('author_id'):
            raise Unauthorized("Only the author can edit this post")
        
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
def delete_post(post_id):
    try:
        user_id = request.headers.get('User-ID')  
        if not UserService.is_admin(user_id):
            raise Unauthorized("Only admins can delete posts")

        forum_service = get_forum_service()
        forum_service.delete_post(post_id)
        return '', 204
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/posts/<int:post_id>/replies', methods=['POST'])
def create_reply(post_id):
    try:
        data = request.json
        if not data or 'content' not in data or 'author_id' not in data:
            raise BadRequest("Content and author_id are required")
        
        forum_service = get_forum_service()
        reply = forum_service.create_reply(data['content'], data['author_id'], post_id)
        return jsonify(reply.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forum_routes.route('/clusters', methods=['POST'])
def create_cluster():
    try:   
        data = request.json
        if not data or 'name' not in data:
            raise BadRequest("Cluster name is required")
        
        forum_service = get_forum_service()
        cluster = forum_service.create_cluster(data['name'], data.get('description'))
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
    