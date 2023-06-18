import json
import os
import sys
import threading

from azure.storage.queue import QueueServiceClient, QueueClient, QueueMessage

from shared_code.services.azure_caption_process import AzureCaption
from shared_code.services.primary_curation_service import PrimaryCurationService
from shared_code.services.secondary_curation_service import SecondaryCurationService

primary_curation_service: PrimaryCurationService = PrimaryCurationService("curationPrimary")
secondary_curation_service: SecondaryCurationService = SecondaryCurationService("curationSecondary")
azure_caption: AzureCaption = AzureCaption()

os.environ["AZURE_QUEUE_ENDPOINT"] = "https://ajdevreddit.queue.core.windows.net/"
os.environ["AZURE_ACCOUNT_KEY"] = "+9066TCgdeVignRdy50G4qjmNoUJuibl9ERiTGzdV4fwkvgdV3aSVqgLwldgZxj/UpKLkkfXg+3k+AStjFI33Q=="


class MessageBroker(threading.Thread):
	def __init__(self, name="curation-message-queue"):
		super().__init__(name=name, daemon=True)
		self.worker_thread = threading.Thread(target=self.run, name="curation-message-queue", daemon=True)
		self.service = QueueServiceClient(account_url=os.environ["AZURE_QUEUE_ENDPOINT"], credential=os.environ["AZURE_ACCOUNT_KEY"])
		self.queue_name: str = name
		self.dlq_name: str = name + "-dlq"

	def try_initialize(self) -> (QueueClient, QueueClient):
		queue = self.service.get_queue_client(self.queue_name)
		dlq = self.service.get_queue_client(self.dlq_name)
		try:
			queue.create_queue()
		except Exception:
			pass
		try:
			dlq.create_queue()
		except Exception:
			pass
		return queue, dlq

	def send_message(self, message: str, queue_name: str = "curation-message-queue"):
		client = self.service.get_queue_client(queue_name)
		client.send_message(message)
		client.close()

	def run_caption_procedure(self, data: dict) -> None:
		image_id = data.get("image_id")
		subreddit = data.get("subreddit")
		action = data.get("action")
		caption = data.get("caption")
		primary_curation_service.update_record(image_id, subreddit=subreddit, action=action, caption=caption,
											   additional_captions=[], relevant_tags=[])
		azure_caption.run_image_process(image_id)
		record = primary_curation_service.get_record_by_id(record_id=image_id, subreddit=subreddit)
		secondary_curation_service.add_new_entry(record)
		azure_caption.run_analysis(image_id=image_id)
		return None

	def run(self):
		try:
			queue_client, dlq_client = self.try_initialize()

			while True:
				messages = queue_client.receive_messages()
				for message in messages:
					try:
						print(f"Processing message: {message.content}")
						data = json.loads(message.content)
						self.run_caption_procedure(data)
						queue_client.delete_message(message)
					except Exception as e:
						print(f"Failed to process message: {message.content}")
						print(f"Error: {str(e)}")
						dlq_client.send_message(message.content)
						queue_client.delete_message(message)
		except Exception as e:
			print(f"Error: {str(e)}")

	def start(self):
		self.worker_thread.start()

	def stop(self):
		sys.exit(0)
