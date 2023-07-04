from flask import Flask
from flask_bootstrap import Bootstrap

from endpoints.api import api_bp
from endpoints.generations import generations_bp
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
app.register_blueprint(generations_bp)
app.register_blueprint(api_bp)
Bootstrap(app)

procs = []

# Initialize message broker
message_broker: MessageBroker = MessageBroker()
procs.append(message_broker)

# Initialize background worker
# collector: RedditImageCollector = RedditImageCollector()
# procs.append(collector)

[item.start() for item in procs]

if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        [item.stop() for item in procs]
