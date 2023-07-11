import json
import random
import sys
import time

import pandas

if __name__ == '__main__':
	from shared_code.storage.tables import TableAdapter

	from tqdm import tqdm
	table_adapter: TableAdapter = TableAdapter()
	client = table_adapter.service.get_table_client("training")
	client_tags = table_adapter.service.get_table_client("relevantTags")
	tags = list(client_tags.query_entities(query_filter="confidence gt 0.5", select=["id, name", "confidence"]))
	tags.sort(key=lambda x: float(x["confidence"]), reverse=True)
	df_tags = pandas.DataFrame(data=tags)

	with tqdm() as pbar:
		for record in client.list_entities():
			record['training_count'] = 0
			record["tags"] = ", ".join([item.get("name") for item in df_tags.where(df_tags["id"] == record["id"]).dropna().to_dict(orient='records')][0:10])
			client.upsert_entity(entity=record)
			pbar.update(1)
		# record["format_caption"] = ""
		# record["caption"] = ""
		# record["GPT"] = ""
		# client.upsert_entity(entity=record)