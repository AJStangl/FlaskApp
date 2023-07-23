import json
import random
from io import BytesIO

import pandas
from flask import Blueprint, send_file

from shared_code.storage.tables import TableAdapter

table_adapter: TableAdapter = TableAdapter()

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/list/tables', methods=['GET'])
def list_tables():
	try:
		result = table_adapter.service.list_tables()
		final = list(result)
		out = pandas.DataFrame(data=final).to_json(orient='records', lines=True).encode("UTF-8")
		io = BytesIO(out)
		io.seek(0)
		return send_file(io, mimetype="application/jsonlines+json")
	except Exception as e:
		return str(e)


@api_bp.route('/api/gpt/training', methods=['GET'])
def gpt():
	client = table_adapter.service.get_table_client("training")
	try:
		gpt_dict_list = list(client.query_entities())
		io = BytesIO()
		for item in gpt_dict_list:
			instances = item['training_count']
			for i in range(instances):
				captions = list(set(item['captions'].split("|")))
				tags = item["tags"]
				title = item['title']
				model = item['PartitionKey']
				for caption in captions:
					training_line = f'<|startoftext|><|model|>{model}<|title|>{title}<|caption|>{caption}<|tags|>{tags}<|endoftext|>\n'
					encoded = training_line.encode("UTF-8")
					io.write(encoded)
		io.seek(0)
		return send_file(io, mimetype="text")
	finally:
		client.close()


@api_bp.route('/api/sd/training/<sub>/<count>/<total>', methods=['GET'])
def training(sub: str, count: int, total: int):
	client = table_adapter.service.get_table_client("training")
	try:
		if sub == 'all':
			query_filter = f"training_count eq {count} and exists eq true and caption ne '' and type eq 'smart'"
		else:
			q = [f"PartitionKey eq '{item}'" for item in sub.split(",")]
			query_filter = " or ".join(q) + f" and training_count eq {count}" + " and exists eq true and type eq 'smart'"

		query_filter = query_filter + " and PartitionKey ne 'CityPorn' and PartitionKey ne 'EarthPorn' and PartitionKey ne 'bathandbodyworks' and PartitionKey ne 'itookapicture' and PartitionKey ne 'memes' and PartitionKey ne 'fatsquirrelhate'"

		entities = list(client.query_entities(query_filter=query_filter))
		entities = [item for item in entities if item['PartitionKey'] != 'CityPorn' or item['PartitionKey'] != 'EarthPorn' or item['PartitionKey'] != 'bathandbodyworks' or item['PartitionKey'] != 'itookapicture' or item['PartitionKey'] != 'memes' or item['PartitionKey'] != 'fatsquirrelhate']
		df = pandas.DataFrame(data=entities)
		records = df.to_dict(orient='records')
		total_records = len(records)
		random_sample_records = []
		for group in df.groupby('PartitionKey', group_keys=False):
			data_values = group[1]
			population = len(data_values) / total_records
			number_to_take = round(population * int(total))
			if number_to_take == 0:
				number_to_take = 1

			if len(data_values) < number_to_take:
				sampled_group = data_values.sample(len(data_values))
			else:
				sampled_group = data_values.sample(number_to_take)

			sample_dict = sampled_group.to_dict(orient='records')
			for elem in sample_dict:
				data_element = {
					"title": elem["title"],
					"subreddit": elem["PartitionKey"],
					"caption": elem["caption"],
					"tags": elem["tags"],
					"path": elem["path"],
					"image": f"{elem['type']}-{elem['path'].split('/')[-1]}",
					"text": f"{elem['title']}, {elem['caption']}, r/{elem['PartitionKey']}, {elem['tags']}"
				}
				random_sample_records.append(data_element)

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
