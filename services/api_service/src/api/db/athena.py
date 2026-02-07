import boto3
import time
from jinja2 import Template
import logging
import json

class AthenaExecutor:
    def __init__(self, region_name="eu-west-2"):
        # self.session = boto3.Session()
        self.client = boto3.client("athena", region_name=region_name)
        # Print the current session's profile, credentials, and region
        # print(f"Using profile: {self.session.profile_name}")
        # credentials = self.session.get_credentials()
        # print(f"AWS Access Key: {credentials.access_key}")
        # print(f"AWS Secret Key: {credentials.secret_key}")
        # print(f"Region: {self.session.region_name}")

    def run_query_and_wait(self, sql_template: str, context: dict,
                           database: str, output_bucket: str):
        
        # Render SQL
        sql = Template(sql_template).render(context)
        print(sql)
        print(json.dumps(context, indent=2))

        # Start query
        response = self.client.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={"Database": database},
            ResultConfiguration={"OutputLocation": f"s3://{output_bucket}"},
            # WorkGroup="primary",
        )
        
        logging.debug(f"Response from Athena: {response}")
        query_id = response["QueryExecutionId"]

        # Wait for completion
        while True:
            status = self.client.get_query_execution(QueryExecutionId=query_id)
            state = status["QueryExecution"]["Status"]["State"]

            if state == "SUCCEEDED":
                break
            if state in ("FAILED", "CANCELLED"):
                reason = status["QueryExecution"]["Status"]["StateChangeReason"]
                raise RuntimeError(f"Athena query failed: {reason}")

            time.sleep(1)

        # Fetch results
        paginator = self.client.get_paginator("get_query_results")
        pages = paginator.paginate(QueryExecutionId=query_id)

        rows = []
        header = None

        for page in pages:
            for row in page["ResultSet"]["Rows"]:
                data = row["Data"]

                # First row is header
                if header is None:
                    header = [col["VarCharValue"] for col in data]
                    continue

                row_dict = {}
                for col_name, value in zip(header, data):
                    row_dict[col_name] = value.get("VarCharValue")

                rows.append(row_dict)

        return rows
