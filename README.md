# Instructions

## Install

With Build Frontend of your choice. e.g. [uv](https://docs.astral.sh/uv)

```
# get uv if not installed
mkdir ~/generator && cd ~/generator
wget https://github.com/astral-sh/uv/releases/download/0.9.25/uv-x86_64-unknown-linux-gnu.tar.gz
tar -xvf uv-x86_64-unknown-linux-gnu.tar.gz
mv uv-x86_64-unknown-linux-gnu/uv .

# install command generator
uv venv --python 3.12
source .venv/bin/activate
uv pip install git+https://github.com/RoboCupAtHome/CommandGenerator
athome-generator --help
```

## Commandline Generator

```
usage: athome-generator [-h] [-d DATA_DIR] [-p]

Generate Commands for Robocup@Home

options:
  -h, --help            show this help message and exit
  -d DATA_DIR, --data-dir DATA_DIR
                        directory where the data is read from
  -p, --print-config    print parsed data and exit
```

Run the generator for the given DATA_DIR
- `athome-generator -d DATA_DIR`

For an example layout check out the: [CompetitionTemplate](https://github.com/RoboCupAtHome/CompetitionTemplate)

## GPSR UI

[nicegui](https://nicegui.io/) UI for GPSR generator. Supports rephrasing via openai compatible llm apis over `http://{host}:{port}/v1/chat/completions`. 

```
athome-generator-gpsr-ui --help
usage: athome-generator-gpsr-ui [-h] [-u URL] [--host HOST] [--port PORT] [-a API_KEY] [-d DATA_DIR]

robocupathome GPSR-UI for usage in competitions

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     Full URL to OpenAI compatible Chat API
  --host HOST           LLM host
  --port PORT           LLM port
  -a API_KEY, --api-key API_KEY
                        LLM API Key
  -d DATA_DIR, --data-dir DATA_DIR
                        directory where the data is read from
```

<img src="docs/gpsr-ui-ref.png" alt="Generate View" style="width:45%; height:auto;">
<img src="docs/gpsr-ui.png" alt="Display View" style="width:45%; height:auto;">