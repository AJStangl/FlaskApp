import json

from flask import Blueprint, render_template, redirect, url_for, request, jsonify

from shared_code.services.primary_curation_service import PrimaryCurationService
from shared_code.services.secondary_curation_service import SecondaryCurationService
from shared_code.azure_storage.tables import TableAdapter

table_adapter: TableAdapter = TableAdapter()
summary_bp = Blueprint('summary', __name__)


@summary_bp.route('/summary/')
def summary():
	try:
		return render_template('summary.jinja2', content=None)
	except Exception as e:
		return render_template('error.jinja2', error=e)


@summary_bp.route('/summary/data', methods=['POST'])
def data():
	query = request.form['query']
	curation_table = table_adapter.get_table_client("curationPrimary")
	entities = list(curation_table.query_entities(query))
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



