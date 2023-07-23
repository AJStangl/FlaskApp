import logging

from flask import Blueprint, render_template, redirect, url_for, request, jsonify

from shared_code.background import message_broker
from shared_code.background.message_broker import MessageBroker
from shared_code.services.secondary_curation_service import SecondaryCurationService

secondary_bp = Blueprint('secondary', __name__)

message_broker: MessageBroker = MessageBroker()
secondary_curation_service: SecondaryCurationService = SecondaryCurationService("curate")


@secondary_bp.route('/secondary/')
def secondary():
	try:
		record = secondary_curation_service.get_next_record()

		if record is None:
			return render_template('error.jinja2', error="No more records to curate")

		else:
			name = record['RowKey']
			subreddit = record['PartitionKey']
			return redirect(url_for('secondary.secondary_image', name=name, subreddit=subreddit))
	except StopIteration:
		return render_template('error.jinja2', error="No more records to curate")
	except Exception as e:
		return render_template('error.jinja2', error=f"An unknown error has occurred: {e}")


@secondary_bp.route('/secondary/image/<name>/<subreddit>', methods=['GET'])
def secondary_image(name, subreddit):
	try:
		record = secondary_curation_service.get_record_by_id(record_id=name, subreddit=subreddit)
		image_link = secondary_curation_service.get_image_url(record_id=record.get('RowKey'), subreddit=record.get('PartitionKey'))
		return render_template('secondary.jinja2', link=image_link, content=record, num_remaining=secondary_curation_service.get_num_remaining_records())
	except Exception as e:
		return render_template('error.jinja2', error=e)


@secondary_bp.route('/secondary/curate/', methods=['POST'])
def secondary_curate():
	image_id = request.form['id']
	subreddit = request.form['subreddit']
	action = request.form['action']

	try:
		if action == 'accept':
			message = {"id": image_id, "partition": subreddit, "action": action, "state": "curate-to-enrich"}
			secondary_curation_service.update_record(image_id, subreddit=subreddit, action=action)
			message_broker.send_message(message, "curate-to-enrich")
			resp = {"redirect": url_for('secondary.secondary')}
			return resp
		else:
			secondary_curation_service.update_record(image_id, subreddit=subreddit, action=action)
			resp = {"redirect": url_for('secondary.secondary')}
			return resp
	except Exception as e:
		return render_template('error.jinja2', error=e)