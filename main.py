from fastapi import FastAPI, Request, Query
from datetime import datetime
from pymongo import MongoClient
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates



app = FastAPI()
app.mount("/static",StaticFiles(directory="static"),name="static")
templates= Jinja2Templates(directory="templates")

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

db1 = client["certdb"]
db2 = client["cert_scanner"]

collection1 = db1["certificates"]  #main certs
collection2 = db2["certificates"]  #root ca

def get_combined_data():
    certs = list(collection1.find({}, {"_id": 0}))
    

    for cert in certs:
        domain = (cert.get("domain") or "").strip().lower()

        

        ca_data = collection2.find_one({"domain": domain},{"_id": 0})

        cert["domain"] = domain  # normalize output
        cert["ca_details"] = ca_data if ca_data else {}


        if cert["ca_details"]:
            cert["ca_details"].pop("domain", None)

    return certs




@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request}
    )


@app.get("/gov.in", response_class=HTMLResponse)
def certificates(request: Request):
    data = get_combined_data()

    return templates.TemplateResponse(
        request,
        "index2.html",
        {"request": request, "certs": data}
    )



