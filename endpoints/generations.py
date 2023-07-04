import json
import logging
import os
import praw
from flask import Blueprint, render_template, request, jsonify, url_for
import io
import requests

from shared_code.azure_storage.tables import TableAdapter

table_adapter: TableAdapter = TableAdapter()

generations_bp = Blueprint('generations', __name__)

logger = logging.getLogger(__name__)


@generations_bp.route('/generations/')
def generations():
	client = table_adapter.service.get_table_client("generations")
	try:
		max_rows = 100
		data = []
		accepted_entities = client.list_entities()
		for elem in accepted_entities:
			if max_rows == 0:
				break
			data.append(dict(elem))
			max_rows -= 1

		data.sort(key=lambda x: x["TimeStamp"], reverse=True)
		subs = get_subs()
		return render_template('generations.jinja2', data=data, subs=list(subs.keys()))
	except Exception as e:
		return render_template('error.jinja2', error=e)
	finally:
		client.close()


@generations_bp.route('/generations/send_to_reddit', methods=['POST'])
def send_to_reddit():
	data = json.loads(request.data.decode("utf-8"))
	path = data["path"]
	title = data["title"]
	sub = data['sub']
	reddit = praw.Reddit(
		client_id=os.environ['client_id'],
		client_secret=os.environ['client_secret'],
		password=os.environ['password'],
		user_agent="script:%(bot_name)s:v%(bot_version)s (by /u/%(bot_author)s)",
		username=os.environ["reddit_username"])
	sub_instance = reddit.subreddit(sub)
	result = requests.get(path, stream=True)
	image_data = io.BytesIO()
	image_data.write(result.content)
	image_data.seek(0)
	with open("temp.png", 'wb') as f:
		f.write(image_data.read())
		submission = sub_instance.submit_image(f"{title}", "temp.png", nsfw=False)
		logger.info(submission)

	return jsonify({
		"success": True,
		"message": f"Sent {path} to {sub} with title {title}"
	})


def get_subs():
	import requests
	return requests.get(url_for("api.list_subs", _external=True)).json()
