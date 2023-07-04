if __name__ == '__main__':
	from shared_code.azure_storage.tables import TableAdapter
	from tqdm import tqdm

	table_adapter: TableAdapter = TableAdapter()
	client = table_adapter.service.get_table_client("curationSecondary")
	results = client.list_entities(select=["PartitionKey"])

	data = []
	for result in tqdm(results):
		if result["PartitionKey"] not in data:
			data.append(result["PartitionKey"])

	print(data)
