import base64
from io import BytesIO

import pandas
from flask import Blueprint, render_template, request, jsonify

from shared_code.azure_storage.tables import TableAdapter
from shared_code.scripts.grapher import GraphingService

table_adapter: TableAdapter = TableAdapter()

summary_bp = Blueprint('summary', __name__)


@summary_bp.route('/summary/')
def summary():
	try:
		tables = list(table_adapter.service.list_tables())
		client = table_adapter.service.get_table_client("training")
		accepted_entities = client.list_entities()
		accepted_entities = list(accepted_entities)
		data_points = []
		for elem in accepted_entities:
			data_points.append(dict(elem))

		df = pandas.DataFrame(data=data_points)

		html = df.to_html()
		image = BytesIO()
		GraphingService.plot_curated_data(accepted_entities).figure.savefig(image, format='png')
		image.seek(0)
		client.close()
		plot_url = base64.b64encode(image.getvalue()).decode('utf8')
		return render_template('summary.jinja2', options=[item.name for item in tables], plot_url=plot_url, table_html=None)
	except Exception as e:
		return render_template('error.jinja2', error=e)


@summary_bp.route('/summary/data', methods=['POST'])
def data():
	query = request.form['query']
	table = request.form['table']
	limit = request.form['limit']
	curation_table = table_adapter.get_table_client(table)
	entities = list(curation_table.query_entities(query, results_per_page=int(limit)))
	entities = entities[0:int(limit)]
	headers = []
	values = []
	for entity in entities:
		for key in entity.keys():
			if key not in headers:
				headers.append(key)
	for entity in entities:
		row = []
		for header in headers:
			row.append(entity.get(header))
		values.append(row)

	return jsonify({
		"headers": headers,
		"data": values
	})
