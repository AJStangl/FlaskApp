import pandas
from azure.data.tables import TableEntity

from shared_code.azure_storage.tables import TableAdapter
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter


class GraphingService(object):
	def __init__(self):
		pass

	def plot_curated_data(self, accepted_entities):
		try:

			data = []
			i = 0
			for entity in accepted_entities:
				table_entity: TableEntity = entity
				table_dict: dict = dict(**table_entity)
				data.append(table_dict)
				i += 1

			df = pandas.DataFrame(data)

			group = df[["id", "model", "subreddit"]].groupby(["subreddit"]).count().sort_values(by="id", ascending=False)

			plot_1 = group.plot.bar(figsize=(20, 10), title="Models with most images", legend=True)
			return plot_1
		finally:
			pass
