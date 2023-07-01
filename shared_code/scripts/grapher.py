import pandas
from azure.data.tables import TableEntity


class GraphingService:
	def __init__(self):
		pass

	@staticmethod
	def plot_curated_data(accepted_entities):
		try:

			data = []
			i = 0
			for entity in accepted_entities:
				table_entity: TableEntity = entity
				table_dict: dict = dict(**table_entity)
				data.append(table_dict)
				i += 1

			df = pandas.DataFrame(data)

			group = df[["RowKey", "PartitionKey"]].groupby(["PartitionKey"]).count().sort_values(by="RowKey", ascending=False)

			plot_1 = group.plot.bar(figsize=(20, 10), title="Models with most images", legend=True)
			return plot_1
		finally:
			pass
