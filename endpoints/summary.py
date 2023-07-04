import base64
import json
from io import BytesIO

import pandas
from flask import Blueprint, render_template, request, jsonify, url_for

from shared_code.azure_storage.tables import TableAdapter

table_adapter: TableAdapter = TableAdapter()

summary_bp = Blueprint('summary', __name__)


@summary_bp.route('/summary/')
def summary():
	client = table_adapter.service.get_table_client("training")
	try:
		tables = list(table_adapter.service.list_tables())

		accepted_entities = client.list_entities()
		accepted_entities = list(accepted_entities)
		data_points = []
		for elem in accepted_entities:
			data_points.append(dict(elem))



		# df = pandas.DataFrame(data=data_points)
		image = BytesIO()
		plot, sub_data = get_stats_graph()

		plot.savefig(image, format='png')
		df = pandas.DataFrame(data=sub_data)
		table_html = df.to_html()
		image.seek(0)
		plot_url = base64.b64encode(image.getvalue()).decode('utf8')
		return render_template('summary.jinja2', options=[item.name for item in tables], plot_url=plot_url, table_html=table_html)
	except Exception as e:
		return render_template('error.jinja2', error=e)

	finally:
		client.close()


@summary_bp.route('/summary/data', methods=['POST'])
def data():
	query = request.form['query']
	table = request.form['table']
	limit = request.form['limit']
	curation_table = table_adapter.get_table_client(table)
	entities = list(curation_table.query_entities(query, results_per_page=int(limit)))
	entities = entities[0:int(limit)]
	headers = []
	values = []
	for entity in entities:
		for key in entity.keys():
			if key not in headers:
				headers.append(key)
	for entity in entities:
		row = []
		for header in headers:
			row.append(entity.get(header))
		values.append(row)

	return jsonify({
		"headers": headers,
		"data": values
	})


def get_stats_graph():
	import requests
	import matplotlib.pyplot as plt
	response = requests.get(url_for("api.list_stats", _external=True)).json()
	subreddit_names = [entry['SubName'] for entry in response]
	trained_values = [entry['Trained'] for entry in response]
	x = range(len(subreddit_names))
	width = 0.25

	fig, ax = plt.subplots()
	rects1 = ax.bar(x, trained_values, width, label='Trained')
	ax.set_ylabel('Count')
	ax.set_title('Subreddit Statistics')
	ax.set_xticks([val + width for val in x])
	ax.set_xticklabels(subreddit_names, rotation=90)
	ax.legend()

	plt.tight_layout()
	return plt, response
