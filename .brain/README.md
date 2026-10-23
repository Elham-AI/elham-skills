# Brain Tooling

Install `python -m pip install -r .brain/requirements.txt`. Clone the required private knowledge vaults into the locations configured by `.brain.json` (or update those paths for your machine). Run `python -X utf8 .brain/scripts/brain_governance.py start . --query <topic>` at session start, read matching notes and the applicable skills, then verify claims against source.

Run `python -m unittest discover -s .brain/tests -v` before publishing governance changes. These tests cover the governance scripts and actual brain routing, not application behavior.
