import inspect
import json
from pathlib import Path

from jinja2 import Environment, BaseLoader
from nbformat.v4 import new_code_cell, new_markdown_cell

import user_templates_api.templates.jupyter_lab.utils.utils as jl_utils
from user_templates_api.utils.client import get_client


class JupyterLabRender:
    def render(self, data):
        # We should append the cells
        # TODO: Check for the template format in metadata.json
        #  and use the appropriate method.

        metadata = data["metadata"]
        data["uuids"] = data.get("uuids", [])

        if metadata["template_format"] == "python":
            cells = self.python_generate_template_data(data)
        elif metadata["template_format"] == "json":
            cells = self.json_generate_template_data(data)
        elif metadata["template_format"] == "jinja":
            cells = self.jinja_generate_template_data(data)

        nb = {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}

        return json.dumps(nb)

    def python_generate_template_data(self, data):
        return []

    def json_generate_template_data(self, data):
        engine = Environment(loader=BaseLoader())

        uuids = data["uuids"]
        group_token = data["group_token"]

        util_client = get_client(group_token)

        template_json = data.get("template")
        if template_json is None:
            class_file_path = inspect.getfile(self.__class__)
            # Convert the string to a pathlib Path
            class_file_path = Path(class_file_path)
            # Grab the parent path and append template.json
            template_file_path = class_file_path.parent / "template.json"
            # Load that filepath since it should be the json template
            template_json = json.load(open(template_file_path))

        cells = []
        for template_item in template_json:
            cell_type = template_item["cell_type"]
            src = template_item["src"]
            if cell_type == "template_cell":
                if src == "get_metadata_cells":
                    cells += jl_utils.get_metadata_cells(uuids, util_client)
                elif src == "get_file_cells":
                    cells += jl_utils.get_file_cells(uuids, util_client)
                elif src == "get_anndata_cells":
                    cells += jl_utils.get_anndata_cells(uuids, util_client)
            elif cell_type == "code_cell":
                template = engine.from_string(src)
                # Need to do something w/ the source to make sure that it has its vars replaced
                # Have to use append here since the nbformat cell object has an add/iadd function that is really a merge
                cells.append(new_code_cell(template.render(**data).strip()))
            elif cell_type == "markdown_cell":
                template = engine.from_string(src)
                # Need to do something w/ the source to make sure that it has its vars replaced
                cells.append(new_markdown_cell(template.render(**data).strip()))

        return cells

    def jinja_generate_template_data(self, data):
        engine = Environment(loader=BaseLoader())

        group_token = data["group_token"]

        data["util_client"] = get_client(group_token)

        # Get the file path first
        class_file_path = inspect.getfile(self.__class__)
        # Convert the string to a pathlib Path
        class_file_path = Path(class_file_path)
        # Grab the parent path and append template.txt
        template_file_path = class_file_path.parent / "template.txt"

        # Load that filepath since it should be the json template
        template_file = open(template_file_path)
        rtemplate = engine.from_string(template_file.read())
        rendered_template = rtemplate.render(**data).strip()
        rendered_template = json.loads(rendered_template) if rendered_template else {}

        # Update this so that it returns actual JSON not text
        return rendered_template
