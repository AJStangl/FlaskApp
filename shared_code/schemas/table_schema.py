class TableFactory:
    def __init__(self):
        pass

    @staticmethod
    def create_primary_entity():
        return {
            'PartitionKey': "",
            'RowKey': "",
            'id': "",
            'subreddit': "",
            'author': "",
            'title': "",
            'caption': "",
            'hash': "",
            'permalink': "",
            'original_url': "",
            'image_name': "",
            'path': "",
            'model': "",
            'exists': False,
            'curated': False,
            'accept': False,
            'tags': "",
        }

    @staticmethod
    def create_secondary_entity(primary_entity: dict):
        return {
            'PartitionKey': primary_entity['subreddit'],
            'RowKey': primary_entity['id'],
            'id': primary_entity['id'],
            'subreddit': primary_entity['subreddit'],
            'author': primary_entity['author'],
            'title': primary_entity['title'],
            'caption': primary_entity['caption'],
            'hash': primary_entity['hash'],
            'permalink': primary_entity['permalink'],
            'original_url': primary_entity['original_url'],
            'image_name': primary_entity['image_name'],
            'path': primary_entity['path'],
            'model': primary_entity['model'],
            'exists': primary_entity['exists'],
            'curated': primary_entity['curated'],
            'accept': primary_entity['accept'],
            'tags': primary_entity['tags'],
            'azure_caption': '',
            'thumbnail_path': '',
            'thumbnail_exists': False,
            'thumbnail_curated': False,
            'thumbnail_accept': False,
            'additional_captions': '',
            'smart_caption': '',
            'best_caption': '',
            'reddit_caption': '',
            'pil_crop_accept': False,
            'azure_crop_accept': False,
            'smart_crop_accept': False,
            'pil_thumbnail_path': '',
            'azure_thumbnail_path': ''
        }

    @staticmethod
    def create_tertiary_entity(subreddit: str,
                               submission_id: str,
                               _type: str,
                               title: str,
                               caption: str,
                               path: str,
                               exists: bool,
                               training_count: int = 0) -> object:
        format_caption = f"{title}, {caption}, in the style of r/{subreddit}"
        gpt = f"<|startoftext|><|model|>{subreddit}<|title|>{title}<|caption|>{format_caption}<|endoftext|>\n"
        return {
            'PartitionKey': subreddit,
            'RowKey': f"{submission_id}-{_type}",
            'id': submission_id,
            'type': _type,
            'title': title,
            'caption': caption,
            'format_caption': format_caption,
            'GPT': gpt,
            'path': path,
            'exists': exists,
            'training_count': training_count
        }

