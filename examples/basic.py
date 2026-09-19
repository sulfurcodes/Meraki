"""Minimal Meraki application.

Run with::

    uvicorn examples.basic:app --reload
"""

from meraki import CORSMiddleware, LoggerMiddleware, Meraki, Plugin

app = Meraki(title="Meraki example", middleware=[LoggerMiddleware(), CORSMiddleware()])


class GreetPlugin(Plugin):
    name = "greet"

    def register(self, plugin_app):
        @plugin_app.get("/plugin-hello")
        def hello(request):
            return {"from": "plugin"}


app.include_plugin(GreetPlugin())


@app.get("/")
def index(request):
    return {"hello": "meraki"}


@app.get("/users/{id:int}")
def get_user(request):
    return {"id": request.path_params["id"]}


@app.post("/echo")
async def echo(request):
    return {"you_sent": await request.json()}
