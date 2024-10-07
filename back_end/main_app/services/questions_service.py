from sqlalchemy.exc import SQLAlchemyError
from main_app.models.models import Question, Answer
from main_app.extensions import db


class QuestionAnswerService:
    @staticmethod
    def create_question(question_text, asker_id):
        try:
            new_question = Question(question=question_text, asker_id=asker_id)
            db.session.add(new_question)
            db.session.commit()
            return new_question
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error creating question: {str(e)}")

    @staticmethod
    def get_question(question_id):
        try:
            return Question.query.get(question_id)
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching question: {str(e)}")

    @staticmethod
    def update_question(question_id, new_question_text=None, is_answered=None):
        try:
            question = Question.query.get(question_id)
            if not question:
                raise Exception("Question not found")
            
            if new_question_text:
                question.question = new_question_text
            
            db.session.commit()
            return question
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error updating question: {str(e)}")

    @staticmethod
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            if not question:
                raise Exception("Question not found")
            
            db.session.delete(question)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting question: {str(e)}")

    @staticmethod
    def create_answer(answer_text, answerer_id, question_id):
        try:
            question = Question.query.get(question_id)
            if question:
                new_answer = Answer(answer=answer_text, answerer_id=answerer_id, question_id=question_id)
                db.session.add(new_answer)
                question.is_answered = True

            else:
                raise Exception("Question not found")
            
            db.session.commit()
            return new_answer
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error creating answer: {str(e)}")

    @staticmethod
    def get_answer(answer_id):
        try:
            return Answer.query.get(answer_id)
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching answer: {str(e)}")

    @staticmethod
    def update_answer(answer_id, new_answer_text):
        try:
            answer = Answer.query.get(answer_id)
            if not answer:
                raise Exception("Answer not found")
            
            answer.answer = new_answer_text
            db.session.commit()
            return answer
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error updating answer: {str(e)}")

    @staticmethod
    def delete_answer(answer_id):
        try:
            answer = Answer.query.get(answer_id)
            if not answer:
                raise Exception("Answer not found")
            
            db.session.delete(answer)
            
            # בדיקה אם יש תשובות נוספות לשאלה
            question = Question.query.get(answer.question_id)
            if question and len(question.answers) == 1:  # אם זו התשובה האחרונה
                question.is_answered = False
            
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting answer: {str(e)}")

    @staticmethod
    def get_unanswered_questions():
        try:
            return Question.query.filter_by(is_answered=False).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching unanswered questions: {str(e)}")

    @staticmethod
    def get_user_questions(user_id):
        try:
            return Question.query.filter_by(asker_id=user_id).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching user questions: {str(e)}")

    @staticmethod
    def get_user_answers(user_id):
        try:
            return Answer.query.filter_by(answerer_id=user_id).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching user answers: {str(e)}")
        