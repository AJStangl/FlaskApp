from flask import Flask
from flask_bootstrap import Bootstrap
from endpoints.index import index_bp
from endpoints.primary import primary_bp
from endpoints.secondary import secondary_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(index_bp)
app.register_blueprint(primary_bp)
app.register_blueprint(secondary_bp)
Bootstrap(app)

if __name__ == '__main__':
    app.run()
