from flask import Flask
from flask_bootstrap import Bootstrap

from endpoints.api import api_bp
from endpoints.generations import generations_bp
from endpoints.index import index_bp
from endpoints.monitor import monitor_bp
from endpoints.primary import primary_bp
from endpoints.secondary import secondary_bp
from endpoints.summary import summary_bp
from shared_code.background.captioning import CaptioningProcesses
from shared_code.background.message_broker import MessageBroker
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger("diffusers").setLevel(logging.DEBUG)
logging.getLogger("azure.storage").setLevel(logging.DEBUG)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Register blueprints
app.register_blueprint(index_bp)
app.register_blueprint(primary_bp)
app.register_blueprint(secondary_bp)
app.register_blueprint(summary_bp)
app.register_blueprint(generations_bp)
app.register_blueprint(api_bp)
app.register_blueprint(monitor_bp)
Bootstrap(app)

procs = []

# Initialize message broker
message_broker: MessageBroker = MessageBroker()
captioning: CaptioningProcesses = CaptioningProcesses()

procs.append(message_broker)
procs.append(captioning)


[item.start() for item in procs]

if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        [item.stop() for item in procs]
