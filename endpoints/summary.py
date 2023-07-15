import base64
from io import BytesIO
from tqdm import tqdm
import pandas
from flask import Blueprint, render_template, request, jsonify
import matplotlib.pyplot as plt
from shared_code.storage.tables import TableAdapter

table_adapter: TableAdapter = TableAdapter()

summary_bp = Blueprint('summary', __name__)


@summary_bp.route('/summary/')
def summary():
	client = table_adapter.service.get_table_client("tempTraining")
	try:
		tables = list(table_adapter.service.list_tables())

		accepted_entities = client.list_entities()
		accepted_entities = list(accepted_entities)
		data_points = []
		for elem in accepted_entities:
			data_points.append(dict(elem))

		image = BytesIO()
		plot, sub_data = get_stats_graph()

		plot.savefig(image, format='png')
		df = pandas.DataFrame(data=sub_data)
		table_html = df.to_html()
		image.seek(0)
		plot_url = base64.b64encode(image.getvalue()).decode('utf8')
		return render_template('summary.jinja2', options=[item.name for item in tables], plot_url=plot_url,
							   table_html=table_html)
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
	response = list_stats()
	subreddit_names = [entry['SubName'] for entry in response]
	trained_values = [entry['Trained'] for entry in response]
	x = range(len(subreddit_names))
	width = 0.25

	fig, ax = plt.subplots()
	ax.bar(x, trained_values, width, label='Trained')
	ax.set_ylabel('Count')
	ax.set_title('Subreddit Statistics')
	ax.set_xticks([val + width for val in x])
	ax.set_xticklabels(subreddit_names, rotation=90)
	ax.legend()

	plt.tight_layout()
	return plt, response


def list_stats(table_name="tempTraining"):
	client = table_adapter.service.get_table_client(table_name)
	records = []
	try:
		list_of_subs = list(client.list_entities(select=['PartitionKey']))
		foo = dict(pandas.DataFrame(data=list_of_subs).groupby("PartitionKey").value_counts())
		for elem in foo:
			try:
				record = {
					"SubName": elem,
					"Trained": 0,
					"Untrained": 0,
					"Total": int(foo[elem]),
					"Percent Influence": float(foo[elem] / sum([foo[item] for item in foo])),
					"Percent Trained Influence": 0.0,
					"All Images": sum([foo[item] for item in foo])
				}
				listing = list(client.query_entities(select=['PartitionKey', "RowKey", "training_count"],
													 query_filter=f"PartitionKey eq '{elem}'"))
				for item in listing:
					if int(item['training_count']) == 0 or item['training_count'] is None:
						record["Untrained"] += 1
					else:
						record["Trained"] += int(item['training_count'])
						record["Percent Trained Influence"] = float(record["Trained"]) / float(record["All Images"])
				records.append(record)
			except Exception as e:
				print(e)
				continue

		return records
	finally:
		client.close()