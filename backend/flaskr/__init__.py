import os
from re import search
from unicodedata import category
from urllib import response
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    """
    CORS set up. Allows '*' for origins. sample route deleted
    """
    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers",
                             "Content-Type,Authorization,true"
                             )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    Endpoint for handling GET requests
    for all available categories.
    """
    @app.route("/categories")
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        # current_categories = paginate_questions(request, selection)
        categories_List = {}

        """
        Category object is not json serializable so must be a
        list just like the todoapp class exercise

        """
        for category in categories:
            categories_List[category.id] = category.type

        if len(categories) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "categories": categories_List,
                "total_categories": len(categories),
            }
        )

    """
    Endpoint for handling GET requests for questions,
    including pagination (every 10 questions).

    """
    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        total_questions = len(selection)
        categories = Category.query.all()
        current_questions = paginate_questions(request, selection)

        if (len(current_questions) == 0):
            abort(404)

        categories = Category.query.all()  # filter(Category.id==Question.id).all()
        categories_List = {}

        for category in categories:
            categories_List[category.id] = category.type

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": total_questions,
                "categories": categories_List,
            }
        )

    """
    Endpoint for deleting question using a question ID.

    """
    @app.route("/questions/<question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            selection = Question.query.order_by(Question.id).all()
            questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": questions,
                    "total_questions": len(Question.query.all()),
                }
            )

        except BaseException:
            abort(404)

    """
    Endpoint to POST a new question,
    and a search for a question
    """
    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_difficulty = body.get("difficulty", None)
        new_category = body.get("category", None)
        search = body.get("searchTerm", None)

        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search))
                )

                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "total_questions": len(Question.query.all())
                    }
                )
            else:
                question = Question(
                    question=new_question,
                    answer=new_answer,
                    difficulty=new_difficulty,
                    category=new_category)
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "created": question.id,
                        "questions": current_questions,
                        "total_questions": len(Question.query.all()),
                    }
                )

        except BaseException:
            abort(422)

    """
    Endpoint to get questions based on category.

    """

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def retrieve_questions_for_each_category(category_id):
        try:
            category = Category.query.filter(
                Category.id == category_id).one_or_none()

            if category is None:
                abort(404)

            selection = Question.query.filter_by(category=category_id).all()
            questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "questions": questions,
                    "total_questions": len(selection),
                }
            )

        except BaseException:
            abort(404)

    """
    Endpoint to get questions to play the quiz.
    This endpoint takes category and previous question parameters
    and return a random questions within the given category
    Wrong indentation affects the output of this endpoint
    """
    @app.route("/quizzes", methods=["POST"])
    def retrieve_quiz():
        body = request.get_json()
        previous_questions = body.get('previous_questions', None)
        quiz_category = body.get('quiz_category', None)

        try:

            if quiz_category['id'] == 0:
                questions = Question.query.order_by(Question.id).all()

                selection = [question.format(
                ) for question in questions if question.id not in previous_questions]

            elif int(quiz_category['id']) in range(7) and (int(quiz_category['id']) != 0):
                questions = Question.query.order_by(Question.id).filter(
                    Question.category == int(quiz_category['id'])).all()

                selection = [question.format(
                ) for question in questions if question.id not in previous_questions]

            if len(selection) == 0:
                return jsonify({
                    "success": False,
                    "question": False,

                })

            else:

                return jsonify({
                    "success": True,
                    "question": random.choice(selection)

                })
        except BaseException:
            abort(404)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def unsuccessful(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "unsuccessful"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(405)
    def badmethod(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    return app
