import pyarrow

curation_schema = pyarrow.schema(
	[
		pyarrow.field("id", pyarrow.string()),
		pyarrow.field("subreddit", pyarrow.string()),
		pyarrow.field("author", pyarrow.string()),
		pyarrow.field("title", pyarrow.string()),
		pyarrow.field("caption", pyarrow.string()),
		pyarrow.field("hash", pyarrow.string()),
		pyarrow.field("permalink", pyarrow.string()),
		pyarrow.field("original_url", pyarrow.string()),
		pyarrow.field("image_name", pyarrow.string()),
		pyarrow.field("path", pyarrow.string()),
		pyarrow.field("model", pyarrow.string()),
		pyarrow.field("exists", pyarrow.bool_()),
		pyarrow.field("curated", pyarrow.bool_()),
		pyarrow.field("accept", pyarrow.bool_()),
		pyarrow.field("tags", pyarrow.list_(pyarrow.string()))
	]
)
