import base64
import json
import logging
import os
import sys
import threading
import time

from azure.storage.queue import QueueServiceClient, QueueClient, BinaryBase64EncodePolicy, BinaryBase64DecodePolicy

from shared_code.services.primary_curation_service import PrimaryCurationService

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logging.getLogger("diffusers").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class MessageBroker(threading.Thread):
	def __init__(self, primary_curation_service, secondary_curation_service, name="curation-message-queue"):
		super().__init__(name=name, daemon=True)
		self.worker_thread = threading.Thread(target=self.run, name="curation-message-queue", daemon=True)
		self.service = QueueServiceClient(account_url=os.environ["AZURE_QUEUE_ENDPOINT"], credential=os.environ["AZURE_ACCOUNT_KEY"])
		self.queue_name: str = name
		self.primary_curation_service = primary_curation_service
		self.secondary_curation_service = secondary_curation_service

	def try_initialize(self) -> QueueClient:
		queue = self.service.get_queue_client(self.queue_name)
		queue.message_encode_policy = BinaryBase64EncodePolicy()
		queue.message_decode_policy = BinaryBase64DecodePolicy()
		# noinspection PyBroadException
		try:
			queue.create_queue()
			return queue
		except Exception:
			return queue
		finally:
			return queue

	def send_message(self, message: str, queue_name):
		client = self.service.get_queue_client(queue_name)
		try:
			client.message_encode_policy = BinaryBase64EncodePolicy()
			client.message_decode_policy = BinaryBase64DecodePolicy()
			dumped = json.dumps(message).encode('utf-8')
			client.send_message(client.message_encode_policy.encode(content=dumped))
		except Exception as e:
			logger.exception(f"Error: {str(e)}")
			return
		finally:
			client.close()

	def run(self):
		try:
			logger.info(f"== Starting message broker for {self.queue_name}==")
			queue_client = self.try_initialize()
			while True:
				try:
					message = queue_client.receive_message()
					if message is None:
						continue
					logger.info(f"Processing message: {message.content}")
					data = json.loads(base64.b64decode(message.content))
					image_id = data["id"]
					subreddit = data["partition"]
					action = data["action"]
					state = data["state"]
					if state == "source-to-primary":
						self.primary_curation_service.update_record(image_id, subreddit, action)
						queue_client.delete_message(message)
					if state == "secondary-to-enrich":
						self.secondary_curation_service.update_record(image_id, subreddit, action)
						queue_client.delete_message(message)
				except Exception as e:
					logger.exception(f"Error: {str(e)}")
					continue
				finally:
					time.sleep(1)

		except Exception as e:
			logger.info(f"Error: {str(e)}")

	def start(self):
		self.worker_thread.start()

	def stop(self):
		sys.exit(0)
