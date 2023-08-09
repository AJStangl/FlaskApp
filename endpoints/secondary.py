import logging

from flask import Blueprint, render_template, redirect, url_for, request, jsonify

from shared_code.background import message_broker
from shared_code.background.message_broker import MessageBroker
from shared_code.services.primary_curation_service import PrimaryCurationService
from shared_code.services.secondary_curation_service import SecondaryCurationService

secondary_bp = Blueprint('secondary', __name__)

primary_curation_service: PrimaryCurationService = PrimaryCurationService("stage")
secondary_curation_service: SecondaryCurationService = SecondaryCurationService("curate")
message_broker: MessageBroker = MessageBroker(primary_curation_service, secondary_curation_service)


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
		secondary_curation_service.records_to_process = None
		return render_template('error.jinja2', error="No more records to curate")
	except Exception as e:
		return render_template('error.jinja2', error=f"An unknown error has occurred: {e}")


@secondary_bp.route('/secondary/image/<name>/<subreddit>', methods=['GET'])
def secondary_image(name, subreddit):
	try:
		record = secondary_curation_service.get_record_by_id(record_id=name, subreddit=subreddit)
		image_link = secondary_curation_service.get_image_url(record_id=record.get('RowKey'), subreddit=record.get('PartitionKey'))
		return render_template('secondary.jinja2', link=image_link, content=record, num_remaining=secondary_curation_service.total_records)
	except Exception as e:
		return render_template('error.jinja2', error=e)


@secondary_bp.route('/secondary/curate/', methods=['POST'])
def secondary_curate():
	image_id = request.form['id']
	subreddit = request.form['subreddit']
	action = request.form['action']

	try:
		message_external = {"id": image_id, "partition": subreddit, "action": action, "state": "curate-to-enrich"}
		message_internal = {"id": image_id, "partition": subreddit, "action": action, "state": "secondary-to-enrich"}
		if action == 'accept':
			message_broker.send_message(message_internal, "source-to-primary")
			message_broker.send_message(message_external, "curate-to-enrich")
			resp = {"redirect": url_for('secondary.secondary')}
			return resp
		else:
			message_broker.send_message(message_internal, "source-to-primary")
			resp = {"redirect": url_for('secondary.secondary')}
			return resp
	except Exception as e:
		return render_template('error.jinja2', error=e)


@secondary_bp.route('/secondary/reset/', methods=['POST'])
def reset():
	secondary_curation_service.reset_records()
	resp = {"redirect": url_for('secondary.secondary')}
	return resp
