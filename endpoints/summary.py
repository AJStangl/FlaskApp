import base64
import random
from io import BytesIO

import matplotlib
import pandas
from flask import Blueprint, render_template, request, jsonify, send_file

from shared_code.azure_storage.tables import TableAdapter
from shared_code.scripts.grapher import GraphingService

table_adapter: TableAdapter = TableAdapter()
from shared_code.schemas.table_schema import TableFactory

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
		return render_template('summary.jinja2', options=[item.name for item in tables], plot_url=plot_url,
							   table_html=html)
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


@summary_bp.route('/summary/gpt', methods=['GET'])
def gpt():
	client = table_adapter.service.get_table_client("training")
	try:
		gpt_dict_list = list(client.list_entities(select=['GPT']))
		io = BytesIO()
		# with open("training.txt", "w", encoding="UTF-8") as out:
		for item in gpt_dict_list:
			line = item["GPT"]
			encoded = line.encode("UTF-8")
			io.write(encoded)

		io.seek(0)
		return send_file(io, mimetype="text")
	finally:
		client.close()


@summary_bp.route('/summary/sample', methods=['GET'])
def sample():
	client = table_adapter.service.get_table_client("training")
	try:
		accepted_data = list(client.list_entities(select=["path", "format_caption", "RowKey", "PartitionKey", "type"]))

		df = pandas.DataFrame(data=accepted_data)

		records = df.to_dict(orient='records')
		total_records = len(records)

		random_sample_records = []

		for group in df.groupby('PartitionKey', group_keys=False):
			sub = group[0]
			data_values = group[1]
			population = len(data_values) / total_records
			number_to_take = round(population * 1000)
			if number_to_take == 0:
				number_to_take = 1

			sampled_group = data_values.sample(number_to_take)
			sample_dict = sampled_group.to_dict(orient='records')
			for elem in sample_dict:
				data_element = {
					"text": elem["format_caption"],
					"path": elem["path"],
					"image": f"{elem['type']}-{elem['path'].split('/')[-1]}"
				}
				random_sample_records.append(data_element)

		random.shuffle(random_sample_records)
		out = pandas.DataFrame(data=random_sample_records).to_json(orient='records', lines=True).encode("UTF-8")
		io = BytesIO(out)
		io.seek(0)
		return send_file(io, mimetype="application/jsonlines+json")
	finally:
		client.close()

