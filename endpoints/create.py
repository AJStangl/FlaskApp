from flask import Blueprint, render_template, request, jsonify, url_for

from shared_code.background.message_broker import SimpleBroker

message_broker: SimpleBroker = SimpleBroker()

create_bp = Blueprint('create', __name__)


@create_bp.route('/create/')
def create():
	try:
		return render_template('create.jinja2')
	except Exception as e:
		return render_template('error.jinja2', error=e)


@create_bp.route('/card', methods=['POST'])
def card():
	data = request.get_json()
	title = data.get('title')
	subreddit = data.get('subreddit')
	prompt = data.get('prompt')
	message_broker.send_message(title, subreddit, prompt)
	resp = {"redirect": url_for('create.create')}
	return jsonify(resp)


