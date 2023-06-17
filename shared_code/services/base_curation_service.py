from abc import ABC, abstractmethod

import pandas

from shared_code.azure_storage.tables import TableAdapter


class BaseService(ABC):
	def __init__(self, table_name: str):
		self.table_name = table_name
		self._table_adapter = TableAdapter()

	@abstractmethod
	def get_table_client(self):
		return self._table_adapter.get_table_client(self.table_name)
