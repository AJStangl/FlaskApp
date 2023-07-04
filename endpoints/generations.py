import json

from flask import Blueprint, render_template, request, jsonify

from shared_code.azure_storage.tables import TableAdapter

table_adapter: TableAdapter = TableAdapter()

generations_bp = Blueprint('generations', __name__)


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

		return render_template('generations.jinja2', data=data)
	except Exception as e:
		return render_template('error.jinja2', error=e)


@generations_bp.route('/generations/send_to_reddit', methods=['POST'])
def send_to_reddit():
	data = json.loads(request.data.decode("utf-8"))
	path = data["path"].split(",")[0]
	title = data["path"].split(",")[1]
	sub = data['sub']
	return jsonify(success=True)
