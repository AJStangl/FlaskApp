from shared_code.azure_storage.tables import TableAdapter
if __name__ == '__main__':
	table_adapter: TableAdapter = TableAdapter()
	table_client = table_adapter.get_table_client("curationSecondary")
	for item in table_client.list_entities():
		pass
		# item.get('pil_')
		# pil_crop_accept = item.get('pil_crop_accept')
		# smart_crop_accept = item.get('smart_crop_accept')
		# azure_crop_accept = item.get('azure_crop_accept')
		# if pil_crop_accept is None:
		# 	item['pil_crop_accept'] = False
		# if smart_crop_accept is None:
		# 	item['smart_crop_accept'] = False
		# if azure_crop_accept is None:
		# 	item['azure_crop_accept'] = False
		# table_client.upsert_entity(item)

