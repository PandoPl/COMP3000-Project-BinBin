from flask import Flask, render_template
from api import api_bp
from db import init_db

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///binbin.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialise database
    init_db(app)

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix = "/api")

    # Dashboard route
    @app.route("/")
    def index():
        return render_template("index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
