import json
import random
from io import BytesIO

import pandas
from flask import Blueprint, send_file

from shared_code.azure_storage.tables import TableAdapter

table_adapter: TableAdapter = TableAdapter()

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/gpt', methods=['GET'])
def gpt():
	client = table_adapter.service.get_table_client("training")
	try:
		gpt_dict_list = list(client.query_entities(
			query_filter="PartitionKey ne 'memes'",
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


@api_bp.route('/api/training/768/<count>', methods=['GET'])
def training_768(count=0):
	client = table_adapter.service.get_table_client("training768")
	try:
		query_filter = f"training_count eq {count}"
		entities = list(client.query_entities(query_filter=query_filter))
		df = pandas.DataFrame(data=entities)
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
				# entity = client.get_entity(partition_key=sub, row_key=elem["RowKey"])
				# current_count = entity['training_count']
				# current_count += 1
				# entity['training_count'] = current_count
				# client.upsert_entity(entity)

		random.shuffle(random_sample_records)
		out = pandas.DataFrame(data=random_sample_records).to_json(orient='records', lines=True).encode("UTF-8")
		io = BytesIO(out)
		io.seek(0)
		return send_file(io, mimetype="application/jsonlines+json")
	finally:
		client.close()


@api_bp.route('/api/diffusion/<sub>/<count>', methods=['GET'])
def diffusion(sub='all', count=0):
	client = table_adapter.service.get_table_client("training")
	try:
		if sub == 'all':
			query_filter = f"training_count eq {count}"
		else:
			query_filter = f"PartitionKey eq '{sub}' and training_count eq {count}"

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


@api_bp.route('/api/list-subs', methods=['GET'])
def list_subs():
	def np_encoder(_object):
		import numpy as np
		if isinstance(_object, np.generic):
			return _object.item()

	client = table_adapter.service.get_table_client("training")
	try:
		list_of_subs = list(client.list_entities(select=['PartitionKey']))
		foo = dict(pandas.DataFrame(data=list_of_subs).groupby("PartitionKey").value_counts())
		io = BytesIO(json.dumps(foo, default=np_encoder).encode("UTF-8"))
		io.seek(0)
		return send_file(io, mimetype="application/json")
	finally:
		client.close()


@api_bp.route('/api/list-stats', methods=['GET'])
def list_stats():
	def np_encoder(_object):
		import numpy as np
		if isinstance(_object, np.generic):
			return _object.item()

	client = table_adapter.service.get_table_client("training")
	records = []

	try:
		list_of_subs = list(client.list_entities(select=['PartitionKey']))
		foo = dict(pandas.DataFrame(data=list_of_subs).groupby("PartitionKey").value_counts())
		for elem in foo:
			record = {
				"SubName": elem,
				"Trained": 0,
				"Untrained": 0,
				"Total": foo[elem]
			}
			listing = list(client.query_entities(select=['PartitionKey', "RowKey", "training_count"],
												 query_filter=f"PartitionKey eq '{elem}'"))
			for item in listing:
				if item['training_count'] == 0:
					record["Untrained"] += 1
				else:
					record["Trained"] += item['training_count']
			records.append(record)

		io = BytesIO(json.dumps(records, default=np_encoder).encode("UTF-8"))
		io.seek(0)
		return send_file(io, mimetype="application/json")
	finally:
		client.close()
