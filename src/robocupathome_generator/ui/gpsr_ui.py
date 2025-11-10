import argparse
from nicegui import Client, ui, events, app, run, ElementFilter
from robocupathome_generator.generator import createGPSRGenerator, dir_path
from robocupathome_generator.gpsr_commands import CommandGenerator
from robocupathome_generator.llm import SimpleOpenaiAPI
import asyncio
import random
import logging
import os.path

logging.basicConfig(filename=os.path.expanduser("~/gpsr-ui.log"),
    filemode='a',
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.ERROR)
logger = logging.getLogger('GPSR-UI')
logger.setLevel(logging.INFO)

from dataclasses import dataclass
@dataclass
class GPSRCommand:
    command: str
    phrasings: list[str]
    kind: str
    

class GPSR_UI():
    number_commands = 3
    enable_ui = True
    generate = True
    commands = []

    def __init__(self, data_dir, server, key):
        self.generator = createGPSRGenerator(data_dir)
        self.llm = SimpleOpenaiAPI(server, key)

    def reconnectLLM(self, server, key):
        self.llm = SimpleOpenaiAPI(server, key)

    async def generateCommand(self, kind = "") -> GPSRCommand:
        command = self.generator.generate_command_start(cmd_category="")
        phrasings = [command]
        return GPSRCommand(command, phrasings, kind)
    
    async def rephraseCommand(self, command: GPSRCommand) -> GPSRCommand:
        phrasings = await run.io_bound(self.llm.alternativePhrasing, command)
        return GPSRCommand(command.command, phrasings, command.kind)
    
    async def buttonRegenerate(self, index):
        old : GPSRCommand = self.commands[index]
        new = await self.generateCommand(old.kind)
        self.commands[index] = new
        commandlist.refresh(self.commands)

    async def buttonReprase(self, index):
        self.enable_ui = False
        old : GPSRCommand = self.commands[index]
        print(f"Rephrasing command...")
        n = ui.notification(message="Rephrasing Command..", timeout=None)
        n.spinner = True
        try:
            command = await self.rephraseCommand(old)
            self.commands[index] = command
            print(f"\trephrased command: {command}")
        except Exception as e:
            n.message = "LLM ERROR"
            logger.error(e)
        commandlist.refresh(self.commands)
        n.spinner = False
        self.enable_ui = True
        n.message = "Done"
        await asyncio.sleep(5)
        n.dismiss()

    async def buttonRephraseAll(self):
        self.enable_ui = False
        print(f"Rephrasing {len(self.commands)} commands...")
        n = ui.notification(message="Rephrasing Command..", timeout=None)
        n.spinner = True
        for i,c in enumerate(self.commands):
            try:
                command = await self.rephraseCommand(c)
                self.commands[i] = command
                print(f"\trephrased {i+1}/{len(self.commands)} commands")
            except Exception as e:
                n.message = "LLM ERROR"
                logger.error(e)
        commandlist.refresh(self.commands)
        n.spinner = False
        self.enable_ui = True
        n.message = "Done"
        await asyncio.sleep(5)
        n.dismiss()

    async def buttonGenerateGPSR(self):
        self.enable_ui = False
        types = ["people", "objects"]
        print(f"Generating {self.number_commands} commands...")
        n = ui.notification(message="Generating Command..", timeout=None)
        self.commands = []
        n.spinner = True
        for i in range(self.number_commands):
            type = types[i] if i < len(types) else ""
            try:
                command = await self.generateCommand(type)
                logger.info(f"Generated command: {command.command}")
                #logger.info(f"Generated phrasings: {command.phrasings}")
                self.commands += [command]
                print(f"\tgenerated {i+1}/{self.number_commands} command: '{command.command}'")
            except Exception as e:
                n.message = "LLM ERROR"
                logger.error(e)

        random.shuffle(self.commands)
        commandlist.refresh(self.commands)

        n.spinner = False
        self.enable_ui = True
        n.message = "Done"
        await asyncio.sleep(5)
        n.dismiss()

    def showCommand(self, i : int):
        print(f"show command: {i}")
        command = self.commands[i]
        basecommand.refresh(command.command, command.phrasings)
        phrasings.refresh(command.phrasings)



def overview():
    commandlist(gpsrui.commands)

def taskview():
    with ui.row():
        ui.label('Text size')
        ui.slider(min=32, max=254, value=128, step=8).props('label-always').on('update:model-value', lambda e: update_label_size(e.args), throttle=0.2).classes('w-128')
    tasklist(gpsrui.commands)

@ui.refreshable
def tasklist(commands: list[GPSRCommand]):
    if not commands:
        ui.label('Please Generate Commands').classes('text-6xl font-bold text-red-600')
    with ui.row():
        commandButtons(commands)
    with ui.row():
        basecommand("", [])
    phrasings([])

@ui.refreshable
def commandlist(commands: list[GPSRCommand]):
    for i,c in enumerate(commands):
        with ui.card().classes('w-full'):
            with ui.row():
                ui.button("New Command", on_click=lambda i=i: gpsrui.buttonRegenerate(i)).bind_enabled_from(gpsrui, 'enable_ui')
                ui.button("Rephrase", on_click=lambda i=i: gpsrui.buttonReprase(i)).bind_enabled_from(gpsrui, 'enable_ui')
            ui.label(f"({c.kind}) {c.command}").classes('text-xl')
            with ui.column():
                for n,p in enumerate(c.phrasings):
                    with ui.row():
                        ui.label("").classes('w-8')
                        ui.label(f"{n}: {p}")

@ui.refreshable
def commandButtons(commands: list[GPSRCommand]):
    for i,c in enumerate(commands):
        ui.button(c.command, on_click=lambda i=i: gpsrui.showCommand(i))

@ui.refreshable
def basecommand(command, phrasings):
    if not command == "":
        with ui.column():
            ui.label(f"Generated: {command}")
            for i,p in enumerate(phrasings):
                ui.label(f"{i}: {p}")

@ui.refreshable
def phrasings(commands):
    with ui.row():
        with ui.tabs().classes('w-full') as tabs2:
            for id, command in enumerate(commands):
                ui.tab(id, label=f"Phrasing {id}")
        
    with ui.tab_panels(tabs2, value='0').classes('w-full h-full'):
        for id, command in enumerate(commands):
            with ui.tab_panel(id).mark('important'):
                ui.label(command).classes('font-bold').style(f'font-size: 128px')

def clickLock():
    print(f"on click: {gpsrui.generate}")
    if gpsrui.generate:
        gpsrui.generate = False
        ui.navigate.to('/task')
    else:
        gpsrui.generate = True
        ui.navigate.to('/')
        

def update_label_size(e):
    print(f"update label size {e}")
    ElementFilter(kind=ui.label).within(marker='important').style(f'font-size: {e}px')

@ui.page('/')
async def root():
    with ui.row().classes('w-full'):
        ui.switch('Lock & Show', value=False).bind_enabled_from(gpsrui, 'enable_ui').on('click', clickLock)
        ui.label("").classes('w-16')
        ui.select([1,2,3,4,5], value=3, label="#").bind_value(gpsrui, 'number_commands').props("dense outlined").bind_enabled_from(gpsrui, 'enable_ui').bind_visibility_from(gpsrui, 'generate')
        ui.button('Generate GPSR Commands', on_click=gpsrui.buttonGenerateGPSR, icon='question_answer').bind_enabled_from(gpsrui, 'enable_ui').bind_visibility_from(gpsrui, 'generate')
        ui.button('Rephrase ALL', on_click=gpsrui.buttonRephraseAll, icon='add_comment').bind_enabled_from(gpsrui, 'enable_ui').bind_visibility_from(gpsrui, 'generate')
        
        
    ui.sub_pages({'/': overview, '/task': taskview}).classes('w-full')

from starlette.responses import HTMLResponse
@app.exception_handler(404)
async def handle_404(request, exc):
    gpsrui.enable_ui = True
    gpsrui.generate = True
    return HTMLResponse(status_code=302, headers={'Location': '/'})


def main():
    pass

if __name__ in {"__main__", "__mp_main__"}:
    main()

parser = argparse.ArgumentParser(description="robocupathome GPSR-UI for usage in competitions")

parser.add_argument(
    "-u", "--url",
    help="Full URL to OpenAI compatible Chat API",
    required=False
)

parser.add_argument(
    "--host",
    help="LLM host",
    default="rhenium"
)

parser.add_argument(
    "--port",
    help="LLM port",
    default="9091"
)

parser.add_argument(
    "-a", "--api-key",
    help="LLM API Key",
    default="tiago"
)

parser.add_argument(
    "-d",
    "--data-dir",
    default="/media/mediassd/projects/robocup/CompetitionTemplate",
    help="directory where the data is read from",
    type=dir_path,
)

args = parser.parse_args()
if args.url:
    if args.host or args.port:
        parser.error("Cannot specify --url together with --host or --port")
else:
    if not (args.host and args.port):
        parser.error("Either --url or both --host and --port must be specified.")

if args.url:
    url = args.url
else:
    url = f"http://{args.host}:{args.port}/v1/chat/completions"

gpsrui = GPSR_UI(args.data_dir, url, args.api_key)
ui.run(show = False)    