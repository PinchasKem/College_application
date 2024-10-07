from flask import jsonify, request, Blueprint, current_app
from main_app.services.questions_service import QuestionAnswerService
from main_app.services.user_service import UserService
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

questions_routes = Blueprint('qa', __name__)

@questions_routes.route('/questions', methods=['POST'])
def create_question(user_id):
    try:
        if UserService.is_guest(user_id):
            raise Unauthorized("Guests cannot create questions")

        data = request.json
        if not data or 'question' not in data:
            raise BadRequest("Question text is required")

        question = QuestionAnswerService.create_question(data['question'], user_id)
        return jsonify(question.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    try:
        question = QuestionAnswerService.get_question(question_id)
        if not question:
            raise NotFound("Question not found")
        return jsonify(question.to_dict()), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id, user_id):
    try:
        question = QuestionAnswerService.get_question(question_id)
        if not question:
            raise NotFound("Question not found")
        
        if not UserService.is_admin(user_id) and question.asker_id != user_id:
            raise Unauthorized("You can only update your own questions or be an admin")

        data = request.json
        if not data:
            raise BadRequest("No data provided")

        updated_question = QuestionAnswerService.update_question(
            question_id, 
            new_question_text=data.get('question')
        )
        return jsonify(updated_question.to_dict()), 200
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id, user_id):
    try:
        question = QuestionAnswerService.get_question(question_id)
        if not question:
            raise NotFound("Question not found")
        
        if not UserService.is_admin(user_id) and question.asker_id != user_id:
            raise Unauthorized("You can only delete your own questions or be an admin")

        QuestionAnswerService.delete_question(question_id)
        return '', 204
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/questions/<int:question_id>/answers', methods=['POST'])
def create_answer(question_id, user_id):
    try:
        if not UserService.is_staff_member(user_id) and not UserService.is_admin(user_id):
            raise Unauthorized("Only staff members or admins can answer questions")

        data = request.json
        if not data or 'answer' not in data:
            raise BadRequest("Answer text is required")

        answer = QuestionAnswerService.create_answer(data['answer'], user_id, question_id)
        return jsonify(answer.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/answers/<int:answer_id>', methods=['PUT'])
def update_answer(answer_id, user_id):
    try:
        if not UserService.is_staff_member(user_id) and not UserService.is_admin(user_id):
            raise Unauthorized("Only staff members or admins can update answers")

        data = request.json
        if not data or 'answer' not in data:
            raise BadRequest("Answer text is required")

        answer = QuestionAnswerService.update_answer(answer_id, data['answer'])
        return jsonify(answer.to_dict()), 200
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/answers/<int:answer_id>', methods=['DELETE'])
def delete_answer(answer_id, user_id):
    try:
        if not UserService.is_staff_member(user_id) and not UserService.is_admin(user_id):
            raise Unauthorized("Only staff members or admins can delete answers")

        QuestionAnswerService.delete_answer(answer_id)
        return '', 204
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/questions/unanswered', methods=['GET'])
def get_unanswered_questions():
    try:
        questions = QuestionAnswerService.get_unanswered_questions()
        return jsonify([q.to_dict() for q in questions]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/users/<int:user_id>/questions', methods=['GET'])
def get_user_questions(user_id):
    try:
        questions = QuestionAnswerService.get_user_questions(user_id)
        return jsonify([q.to_dict() for q in questions]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@questions_routes.route('/users/<int:user_id>/answers', methods=['GET'])
def get_user_answers(user_id):
    try:
        answers = QuestionAnswerService.get_user_answers(user_id)
        return jsonify([a.to_dict() for a in answers]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    