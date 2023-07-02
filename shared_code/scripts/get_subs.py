from azure.data.tables import TableClient
from shared_code.azure_storage.tables import TableAdapter


if __name__ == '__main__':
	subs = []
	table_client: TableClient = TableAdapter().get_table_client("curationSecondary")
	for elem in table_client.list_entities(select=["PartitionKey"]):
		sub = elem["PartitionKey"]
		if sub in subs:
			continue
		else:
			subs.append(sub)
	print(subs)