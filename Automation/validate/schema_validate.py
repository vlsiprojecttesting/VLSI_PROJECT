"""
File:schema_validate.py
Description:Validates a YAML dictionary against a JSON schema.
Author:Balasaraswathy B
"""
import json
try:
    import jsonschema
except ImportError:
    raise ImportError("The 'jsonschema' package is required. Install it with 'pip install jsonschema'.")
"""
Function:validate_yaml_schema
Description:Validates a YAML dictionary against a JSON schema.
@param yaml_dict:Dictionary representation of the YAML file.
@param schema_path:Path to the JSON schema file.
@return:None
"""
def validate_yaml_schema(yaml_dict: dict, schema_path: str) -> None:
    with open(schema_path, "r") as f:
        schema = json.load(f)
    jsonschema.validate(instance=yaml_dict, schema=schema)
