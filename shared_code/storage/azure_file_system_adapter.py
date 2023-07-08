from adlfs import AzureBlobFileSystem
import os


class AzureFileStorageAdapter(object):
	def __init__(self, container_name: str):
		self._account_name: str = os.environ["AZURE_ACCOUNT_NAME"]
		self._account_key: str = os.environ["AZURE_ACCOUNT_KEY"]
		self.container_name: str = container_name

	def get_file_storage(self) -> AzureBlobFileSystem:
		return AzureBlobFileSystem(
			account_name=self._account_name,
			account_key=self._account_key,
			container_name=self.container_name)

