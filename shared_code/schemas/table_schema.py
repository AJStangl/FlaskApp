from azure.data.tables import TableEntity
import pandas as pd
import numpy as np
import json


class CurationEntity(TableEntity):
    def __init__(self, partition_key=None, row_key=None):
        super().__init__(PartitionKey=partition_key, RowKey=row_key)
        self.id: str = None
        self.subreddit: str = None
        self.author: str = None
        self.title: str = None
        self.caption: str = None
        self.hash: str = None
        self.permalink: str = None
        self.original_url: str = None
        self.image_name: str = None
        self.path: str = None
        self.model: str = None
        self.exists: bool = False
        self.curated: bool = False
        self.accept: bool = False
        self.tags: [] = None

    @classmethod
    def from_dict(cls, properties) -> 'CurationEntity':
        entity = cls(properties.get('subreddit'), properties.get('id'))
        entity.id = properties.get('id')
        entity.subreddit = properties.get('subreddit')
        entity.author = properties.get('author')
        entity.title = properties.get('title')
        entity.caption = properties.get('caption')
        entity.hash = properties.get('hash')
        entity.permalink = properties.get('permalink')
        entity.original_url = properties.get('original_url')
        entity.image_name = properties.get('image_name')
        entity.path = properties.get('path')
        entity.model = properties.get('model')
        entity.exists = properties.get('exists')
        entity.curated = properties.get('curated')
        entity.accept = properties.get('accept')
        entity.tags = properties.get('tags')
        return entity

    def to_dict(self) -> dict:
        properties = {
            'PartitionKey': self.subreddit,
            'RowKey': self.id,
            'id': self.id,
            'subreddit': self.subreddit,
            'author': self.author,
            'title': self.title,
            'caption': self.caption,
            'hash': self.hash,
            'permalink': self.permalink,
            'original_url': self.original_url,
            'image_name': self.image_name,
            'path': self.path,
            'model': self.model,
            'exists': self.exists,
            'curated': self.curated,
            'accept': self.accept,
            'tags': self.tags,
        }
        return properties

    @classmethod
    def from_dataframe(cls, dataframe: pd.DataFrame) -> list:
        entities = []
        for _, row in dataframe.iterrows():
            entity = cls(partition_key=row['subreddit'], row_key=row['id'])
            for column in dataframe.columns:
                if isinstance(row[column], np.ndarray) or isinstance(row[column], list):
                    value = list(row[column])
                    value = json.dumps(value)
                    entity[column] = value
                else:
                    entity[column] = row[column]
            entities.append(entity)
        return entities

    def to_dataframe(self) -> pd.DataFrame:
        data = {}
        attributes = vars(self)

        for attr_name, attr_value in attributes.items():
            if isinstance(attr_value, list):
                data[attr_name] = [json.dumps(attr_value)]
            else:
                data[attr_name] = [attr_value]

        return pd.DataFrame(data)


class PrimaryCurationEntity(CurationEntity):
    def __init__(self, partition_key, row_key):
        super().__init__(partition_key, row_key)

    def to_dict(self):
        properties = super().to_dict()
        properties['tags'] = json.dumps(properties['tags'])
        return properties


class SecondaryCurationEntity(PrimaryCurationEntity):
    def __init__(self, partition_key=None, row_key=None):
        super().__init__(partition_key, row_key)
        self.azure_caption: str = None
        self.thumbnail_path: str = None
        self.thumbnail_exists: bool = False
        self.thumbnail_curated: bool = False
        self.thumbnail_accept: bool = False
        self.additional_captions: [] = None

