import base64
import json
import random
from io import BytesIO

import matplotlib
import pandas
from flask import Blueprint, render_template, request, jsonify, send_file

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


@summary_bp.route('/summary/gpt', methods=['GET'])
def gpt():
	client = table_adapter.service.get_table_client("training")
	try:
		gpt_dict_list = list(client.query_entities(
			query_filter="PartitionKey ne 'memes' and PartitionKey ne 'itookapicture' and PartitionKey ne 'EarthPorn' and PartitionKey ne 'CityPorn'",
			select=['GPT']))
		io = BytesIO()
		for item in gpt_dict_list:
			line = item["GPT"]
			encoded = line.encode("UTF-8")
			io.write(encoded)
		io.seek(0)
		return send_file(io, mimetype="text")
	finally:
		client.close()


@summary_bp.route('/summary/diffusion/<sub>', methods=['GET'])
def diffusion(sub='all'):
	client = table_adapter.service.get_table_client("training")
	try:
		if sub == 'all':
			query_filter = "training_count eq 0"
		else:
			query_filter = f"PartitionKey eq '{sub}'"

		accepted_data = list(client.query_entities(query_filter=query_filter,
												   select=["path", "format_caption", "RowKey", "PartitionKey", "type",
														   "training_count"]))

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

			if len(data_values) < number_to_take:
				sampled_group = data_values.sample(len(data_values))
			else:
				sampled_group = data_values.sample(number_to_take)

			sample_dict = sampled_group.to_dict(orient='records')
			for elem in sample_dict:
				data_element = {
					"text": elem["format_caption"],
					"path": elem["path"],
					"image": f"{elem['type']}-{elem['path'].split('/')[-1]}"
				}
				random_sample_records.append(data_element)
				entity = client.get_entity(partition_key=sub, row_key=elem["RowKey"])
				current_count = entity['training_count']
				current_count += 1
				entity['training_count'] = current_count
				client.upsert_entity(entity)

		random.shuffle(random_sample_records)
		out = pandas.DataFrame(data=random_sample_records).to_json(orient='records', lines=True).encode("UTF-8")
		io = BytesIO(out)
		io.seek(0)
		return send_file(io, mimetype="application/jsonlines+json")
	finally:
		client.close()


@summary_bp.route('/summary/list-subs', methods=['GET'])
def list_subs():
	def np_encoder(object):
		import numpy as np
		if isinstance(object, np.generic):
			return object.item()
	client = table_adapter.service.get_table_client("training")
	try:
		list_of_subs = list(client.list_entities(select=['PartitionKey']))
		foo = dict(pandas.DataFrame(data=list_of_subs).groupby("PartitionKey").value_counts())
		io = BytesIO(json.dumps(foo, default=np_encoder).encode("UTF-8"))
		io.seek(0)
		return send_file(io, mimetype="application/json")
	finally:
		client.close()
