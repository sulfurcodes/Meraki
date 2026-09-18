from meraki import Meraki
from meraki.core.response import Response

app = Meraki()

@app.get("/")
async def home(request):
    return Response(body=b"Hello from Meraki!")

@app.post("/users")
async def create_user(request):
    return Response(body=b"User created", status_code=201)

# To run the development server:
# $ uvicorn example:app
