from flask import jsonify, url_for, Blueprint, render_template

from shared_code.storage.tables import TableAdapter
from shared_code.background.reddit_collection import RedditImageCollector

table_adapter: TableAdapter = TableAdapter()
reddit_collector: RedditImageCollector = RedditImageCollector()

monitor_bp = Blueprint('monitor', __name__)


@monitor_bp.route('/monitor/')
def monitor():
	data = {
		"status": reddit_collector.process is not None,
		"records": reddit_collector.records_processed
	}
	return render_template('monitor.jinja2', data=data)


@monitor_bp.route('/api/monitor/<state>', methods=['GET'])
def collect(state):
	if state == "start":
		if reddit_collector.process is not None:
			return jsonify({
				"status": reddit_collector.process is not None,
				"message": "Already collecting",
				"redirect": url_for("monitor.monitor")
			})
		else:
			reddit_collector.start()
			return jsonify({
				"success": reddit_collector.process is not None,
				"message": "Started collecting",
				"redirect": url_for("monitor.monitor")
			})
	else:
		reddit_collector.stop()
		return jsonify({
			"success": reddit_collector.process is not None,
			"message": "Stopped collecting",
			"redirect": url_for("monitor.monitor")
		})
