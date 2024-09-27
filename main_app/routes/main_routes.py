from flask import Blueprint, jsonify
from main_app.routes.user_routes import user_routes
from main_app.routes.events_routes import events_routes
from main_app.routes.forum_routes import forum_routes
from main_app.routes.lesson_routes import lessons_routes
from main_app.routes.questions_routes import questions_routes

main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    return jsonify({"message": "Welcome to the Seminary System API"})

def register_routes(app):
    app.register_blueprint(main_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(events_routes)
    app.register_blueprint(forum_routes)
    app.register_blueprint(lessons_routes)
    app.register_blueprint(questions_routes)
