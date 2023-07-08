import random
import sys
import time

import pandas

if __name__ == '__main__':
	from shared_code.storage.tables import TableAdapter
	from shared_code.storage.azure_file_system_adapter import AzureFileStorageAdapter, AzureBlobFileSystem
	from shared_code.background.reddit_collection import RedditImageCollector
	from tqdm import tqdm

	# collector = RedditImageCollector()
	# collector.start()
	# time.sleep(5)
	# collector.stop()
	# collector.start()
	# time.sleep(5)
	# collector.stop()
	file_system: AzureBlobFileSystem = AzureFileStorageAdapter('data').get_file_storage()
	table_adapter: TableAdapter = TableAdapter()
	client = table_adapter.service.get_table_client("training768")

	print("Getting entities")
	listing = list(client.list_entities())
	for record in tqdm(listing, total=len(listing)):
		record['training_count'] = 0
		record['id'] = record['RowKey'].split("-")[0]
		record['exists'] = file_system.exists(record['path'])
		client.upsert_entity(entity=record)
	print("Done")
	sys.exit(0)
	# client_tags = table_adapter.service.get_table_client("relevantTags")
	# client_secondary = table_adapter.service.get_table_client("curationSecondary")
	#
	# tags = list(client_tags.query_entities(query_filter="confidence gt 0.75", select=["id, name"]))
	# df_tags = pandas.DataFrame(data=tags)
	# records = list(client.list_entities())
	# for record in tqdm(records, total=len(records)):
	# 	subreddit = record["PartitionKey"]
	# 	row_key = record["RowKey"]
	# 	image_type = record["type"]
	# 	title = record['title']
	# 	record_id = row_key.replace(image_type, "").replace("-", "").strip()
	# 	tags_to_use = ", ".join([item.get("name") for item in df_tags.where(df_tags["id"] == record_id).dropna().to_dict(orient='records')])
	# 	primary_record = client_secondary.get_entity(partition_key=subreddit, row_key=record_id)
	# 	azure_caption = primary_record.get("azure_caption")
	# 	pil_caption = primary_record.get("pil_caption")
	# 	smart_caption = primary_record.get("smart_caption")
	# 	all_captions = [item for item in [azure_caption, pil_caption, smart_caption] if item is not None]
	#
	# 	random_selection = random.choice(all_captions)
	#
	# 	image_description = f"{random_selection}, {tags_to_use}"
	# 	gpt_string = f"<|startoftext|><|model|>{subreddit}<|title|>{title}<|caption|>{image_description}<|endoftext|>"
	# 	record["GPT"] = gpt_string
	# 	record["format_caption"] = image_description
	# 	client.upsert_entity(record)
	# 	print(image_description)

