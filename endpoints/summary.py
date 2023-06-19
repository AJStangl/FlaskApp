from flask import Blueprint, render_template, request, jsonify

from shared_code.azure_storage.tables import TableAdapter

table_adapter: TableAdapter = TableAdapter()
summary_bp = Blueprint('summary', __name__)


@summary_bp.route('/summary/')
def summary():
	try:
		tables = list(table_adapter.service.list_tables())
		return render_template('summary.jinja2', options=[item.name for item in tables])
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



