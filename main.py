# Production would enforce https
# Logging/auditing would be added as well.
# Rate Limiting/API gateway should also be implemented 
from flask_jwt_extended import JWTManager
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from decouple import config
from extensions import db
from users import users_bp
from transactions import transactions_bp


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
app.config['JWT_SECRET_KEY'] = config('JWT_SECRET_KEY')
app.config['SWAGGER'] = {
    'uiversion': 3,
    'openapi': '3.0.2',
    'doc_dir': './docs'
}

swagger_template = {
    "info": {
        "title": "Fintech API by Erik Pfankuch",
        "description": "API for user authentication and transactions",
        "version": "1.0.0"
    },
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
            }
        }
    },
    "security": [{"BearerAuth": []}]
}

swagger = Swagger(app, template=swagger_template)

CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000"]) 
# Obviously configure CORS for whatever origins are needed for a live application
db.init_app(app)
jwt = JWTManager(app)


# Route registration
app.register_blueprint(users_bp, url_prefix='/api/v1/users')
app.register_blueprint(transactions_bp, url_prefix='/api/v1/users')


# This would be used in production to ensure server header doesn't leak version/technology information
# but we're running this in debug mode for example and it currently doesn't do anything because werkzeug
# overrides it
@app.after_request
def remove_server_header(response):
    # Overwrite or remove headers that reveal tech stack
    response.headers["Server"] = "secure"  # or remove: del response.headers["Server"]
    response.headers.pop("X-Powered-By", None)
    return response


if __name__ == "__main__":
    app.run(debug=True)
