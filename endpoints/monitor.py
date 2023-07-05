from flask import jsonify, url_for, Blueprint, render_template

from shared_code.azure_storage.tables import TableAdapter
from shared_code.background.reddit_collection import RedditImageCollector

table_adapter: TableAdapter = TableAdapter()
reddit_collector: RedditImageCollector = RedditImageCollector()

monitor_bp = Blueprint('monitor', __name__)


@monitor_bp.route('/monitor/')
def monitor():
	data = {
		"status": reddit_collector.worker_thread.is_alive(),
		"records": reddit_collector.records_processed
	}
	return render_template('monitor.jinja2', data=data)


@monitor_bp.route('/api/monitor/<state>', methods=['GET'])
def collect(state):
	if state == "start":
		if reddit_collector.worker_thread.is_alive():
			return jsonify({
				"status": reddit_collector.worker_thread.is_alive(),
				"message": "Already collecting",
				"redirect": url_for("monitor.monitor")
			})
		else:
			reddit_collector.worker_thread.start()
			return jsonify({
				"success": reddit_collector.worker_thread.is_alive(),
				"message": "Started collecting",
				"redirect": url_for("monitor.monitor")
			})
	else:
		reddit_collector.worker_thread.join()
		return jsonify({
			"success": reddit_collector.worker_thread.is_alive(),
			"message": "Stopped collecting",
			"redirect": url_for("monitor.monitor")
		})
