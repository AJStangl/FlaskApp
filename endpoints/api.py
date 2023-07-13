import json
import random
from io import BytesIO

import pandas
from flask import Blueprint, send_file

from shared_code.storage.tables import TableAdapter
from shared_code.storage.azure_file_system_adapter import AzureFileStorageAdapter, AzureBlobFileSystem

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



@api_bp.route('/api/gpt/<table>', methods=['GET'])
def gpt(table: str):
	client = table_adapter.service.get_table_client(table)
	try:
		gpt_dict_list = list(client.query_entities(query_filter="training_count gt 0 and caption ne ''", select=["PartitionKey", "title", "caption", "tags"]))
		io = BytesIO()
		for item in gpt_dict_list:
			training_line = f'<|startoftext|><|model|>{item["PartitionKey"]}<|title|>{item["title"]}<|caption|>{item["caption"]}<|tags|>{item["tags"]}<|endoftext|>\n'
			encoded = training_line.encode("UTF-8")
			io.write(encoded)
		io.seek(0)
		return send_file(io, mimetype="text")
	finally:
		client.close()


@api_bp.route('/api/training/768/<sub>/<count>/<total>', methods=['GET'])
def training_768(sub, count, total):
	client = table_adapter.service.get_table_client("training768")
	try:
		if sub == 'all':
			query_filter = f"training_count eq {count} and exists eq true and caption ne ''"
		else:
			q = [f"PartitionKey eq '{item}'" for item in sub.split(",")]
			query_filter = " or ".join(q) + f" and training_count eq {count}" + " and exists eq true"

		entities = list(client.query_entities(query_filter=query_filter))
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


@api_bp.route('/api/training/<sub>/<count>/<total>', methods=['GET'])
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


@api_bp.route('/api/768/list-stats', methods=['GET'])
def list_768_stats():
	def np_encoder(_object):
		import numpy as np
		if isinstance(_object, np.generic):
			return _object.item()

	client = table_adapter.service.get_table_client("training768")
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
				if item.get('training_count') is None:
					continue
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


@api_bp.route('/api/768/complete-runs', methods=['GET'])
def complete_runs():
	client = table_adapter.service.get_table_client("training768")
	file_system: AzureBlobFileSystem = AzureFileStorageAdapter("data").get_file_storage()
	try:
		runs_to_complete = file_system.ls("data/prior_runs")
		completed_data = []
		for run in runs_to_complete:
			try:
				with file_system.open(run, 'r', encoding="utf-8") as f:
					try:
						content = f.readlines()
						for line in content:
							try:
								data = json.loads(line)
								image_type, image_id = data["image"].split("-")[0], data["image"].split("-")[1]
								image_id_final = image_id.split(".")[0] + f"-{image_type}"
								partition_key = data["subreddit"]
								entity = client.get_entity(partition_key=partition_key, row_key=image_id_final)
								training_count = int(entity["training_count"])
								training_count += 1
								entity["training_count"] = training_count
								client.upsert_entity(entity)
								completed_data.append(data)
							except Exception as e:
								print(e)
								continue
					except Exception as e:
						print(e)
						continue
				file_system.delete(run)
			except Exception as e:
				print(e)
				continue
		return completed_data
	finally:
		client.close()