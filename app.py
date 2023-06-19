from flask import Flask
from flask_bootstrap import Bootstrap
from endpoints.index import index_bp
from endpoints.primary import primary_bp
from endpoints.secondary import secondary_bp
from endpoints.summary import summary_bp
from shared_code.background.message_broker import MessageBroker

app = Flask(__name__)

# Register blueprints
app.register_blueprint(index_bp)
app.register_blueprint(primary_bp)
app.register_blueprint(secondary_bp)
app.register_blueprint(summary_bp)
Bootstrap(app)

# Initialize message broker
message_broker: MessageBroker = MessageBroker()
message_broker.start()

if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        message_broker.stop()
