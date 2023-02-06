from __future__ import annotations

from pathlib import Path

import aws_cdk as cdk
import tomli
from aws_cdk import Tags

from cdk.stack_q_box import QBoxStack

pyproject_path = Path.cwd() / "pyproject.toml"
with pyproject_path.open("rb") as f:
    pyproject = tomli.load(f)

project_name = pyproject["project"]["name"].replace("_", "-")

app = cdk.App()
apigw_stack = QBoxStack(app, project_name)
Tags.of(apigw_stack).add("Project", project_name)
Tags.of(apigw_stack).add("Type", "dev")
Tags.of(apigw_stack).add("Creator", "cdk")
app.synth()
