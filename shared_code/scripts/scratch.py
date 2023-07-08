import json
import random
import sys
import time

import pandas

if __name__ == '__main__':
	from shared_code.storage.tables import TableAdapter

	from tqdm import tqdm
	table_adapter: TableAdapter = TableAdapter()
	client = table_adapter.service.get_table_client("training768")
	client_tags = table_adapter.service.get_table_client("relevantTags")
	tags = list(client_tags.query_entities(query_filter="confidence gt 0.5", select=["id, name"]))
	df_tags = pandas.DataFrame(data=tags)
	records = list(client.list_entities())
	for record in tqdm(records, total=len(records)):
		record["tags"] = ", ".join([item.get("name") for item in df_tags.where(df_tags["id"] == record["id"]).dropna().to_dict(orient='records')])
		record["format_caption"] = ""
		record["caption"] = ""
		record["GPT"] = ""
		client.upsert_entity(entity=record)