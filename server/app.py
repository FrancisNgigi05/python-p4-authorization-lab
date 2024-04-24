#!/usr/bin/env python3
from flask import abort
from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

@app.before_request
def chck_if_logged_id():
    open_access_list = ['clear', 'article_list', 'show_article', 'login', 'log_out', 'check_session']

    if request.endpoint not in open_access_list and not session.get('user_id'):
        return {"error": "401 Unauthorized"}, 401
class ClearSession(Resource):

    def delete(self):
    
        session['page_views'] = None
        session['user_id'] = None

        return {}, 204

class IndexArticle(Resource):
    
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return make_response(jsonify(articles), 200)

class ShowArticle(Resource):

    def get(self, id):

        article = Article.query.filter(Article.id == id).first()
        article_json = article.to_dict()

        if not session.get('user_id'):
            session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
            session['page_views'] += 1

            if session['page_views'] <= 3:
                return article_json, 200

            return {'message': 'Maximum pageview limit reached'}, 401

        return article_json, 200

class Login(Resource):

    def post(self):
        
        username = request.get_json().get('username')
        user = User.query.filter(User.username == username).first()

        if user:
        
            session['user_id'] = user.id
            return user.to_dict(), 200

        return {}, 401

class Logout(Resource):

    def delete(self):

        session['user_id'] = None
        
        return {}, 204

class CheckSession(Resource):

    def get(self):
        
        user_id = session['user_id']
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return user.to_dict(), 200
        
        return {}, 401

# This is a view where one will be able to only see the members only articles
class MemberOnlyIndex(Resource):
    def get(self):
        # Where I will be appending the articles
        data = []
        # Getting the articles which are for members only
        for article in Article.query.filter(Article.is_member_only == True).all():
            # Converting each article to a dict
            article_dict = article.to_dict()
            # Appening the dict to the data array
            data.append(article_dict)

        response = make_response(data, 200)
        return response


# This is just a view that a logged_in user can be access any article of their liking without any restrictions
class MemberOnlyArticle(Resource):
    def get(self, id):
        # Getting the required article requested by the logged in user
        article = Article.query.filter(Article.id == id).first()
        # Coverting that article ot a dict
        article_dict = article.to_dict()
        # Generating the response
        response = make_response(article_dict, 200)

        return response

api.add_resource(ClearSession, '/clear', endpoint='clear')
api.add_resource(IndexArticle, '/articles', endpoint='article_list')
api.add_resource(ShowArticle, '/articles/<int:id>', endpoint='show_article')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(MemberOnlyIndex, '/members_only_articles', endpoint='member_index')
api.add_resource(MemberOnlyArticle, '/members_only_articles/<int:id>', endpoint='member_article')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
