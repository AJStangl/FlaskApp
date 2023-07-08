import abc

from shared_code.storage.tables import TableAdapter


class BaseService(abc.ABC):
	def __init__(self, table_name: str):
		self.table_name = table_name
		self._table_adapter = TableAdapter()

	@abc.abstractmethod
	def get_table_client(self):
		return self._table_adapter.get_table_client(self.table_name)
