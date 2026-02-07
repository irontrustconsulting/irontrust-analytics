# api/registry.py
import json
import boto3
from api.models.models import TemplateRegistry, QueryTemplate

class QueryRegistry:
    def __init__(self, config):
        """
        Initialize the registry using bucket and prefix from AppConfig
        """
        self.templates: TemplateRegistry = self._load_templates_from_s3(
            bucket=config.sql_template_bucket,
            prefix=config.sql_template_prefix
        )

    def _load_templates_from_s3(self, bucket: str, prefix: str) -> TemplateRegistry:
        s3 = boto3.client("s3")
        object_list = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

        templates = []

        for obj in object_list.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/") or not key.lower().endswith(".json"):
                continue

            obj_data = s3.get_object(Bucket=bucket, Key=key)
            content = obj_data["Body"].read().decode("utf-8")
            template_data = json.loads(content)
            templates.append(QueryTemplate(**template_data))

        return TemplateRegistry(registry=templates)

    def get_template(self, template_id: str) -> QueryTemplate | None:
        return self.templates.get_template(template_id)

    def list_templates(self) -> list[str]:
        return self.templates.list_templates()
