from azure.data.tables import TableClient
from tqdm import tqdm

from shared_code.azure_storage.tables import TableAdapter
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter, AzureBlobFileSystem
from shared_code.services.training_service import TrainingService

if __name__ == '__main__':

	file_system: AzureBlobFileSystem = AzureFileStorageAdapter("data").get_file_storage()

	table_client: TableClient = TableAdapter().get_table_client("curationSecondary")

	training_service: TrainingService = TrainingService()

	accepted_entities = list(table_client.query_entities("thumbnail_accept eq true"))

	for record in tqdm(accepted_entities, total=len(accepted_entities)):
		training_service.upsert_data_record(record['subreddit'], record['id'])
