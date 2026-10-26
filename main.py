import csv
import io
import os
import re
from datetime import datetime, timedelta, timezone
from math import ceil
from urllib.parse import urlencode

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient

load_dotenv()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = MongoClient(os.getenv("MONGOURL"))
collection1 = client["certdb"]["certificates"]        # leaf certificate data
collection2 = client["cert_scanner"]["certificates"]  # chain / root CA data

SORTS = {"domain": "domain", "issuer": "issuer", "ca": "ca_id", "exp": "valid_to"}


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def field(s, key="CN"):
    m = re.search(r"(?:^|[,(])" + key + r"=([^,)>]+)", s or "")
    return m.group(1) if m else ""


def build_filter(q="", status="all", issuer=""):
    f, now = {}, utcnow()
    if q:
        f["domain"] = {"$regex": re.escape(q.strip().lower())}
    if status == "expired":
        f["valid_to"] = {"$lt": now}
    elif status == "soon":
        f["valid_to"] = {"$gte": now, "$lte": now + timedelta(days=30)}
    elif status == "valid":
        f["valid_to"] = {"$gt": now + timedelta(days=30)}
    if issuer:
        f["issuer"] = {"$regex": "CN=" + re.escape(issuer) + "[,)]"}
    return f


def decorate(c, ca_map, now):
    c["domain"] = (c.get("domain") or "").strip().lower()
    iss = c.get("issuer") or ""
    c["issuer_cn"] = field(iss) or field(iss, "O") or "Unknown"
    c["issuer_org"] = field(iss, "O")
    to = c.get("valid_to")
    if to:
        days = (to.replace(tzinfo=None) - now).days
        c["status"] = "expired" if days < 0 else "soon" if days <= 30 else "valid"
        c["label"] = f"Expired {-days} days ago" if days < 0 else f"{days} days left"
    else:
        c["status"], c["label"] = "unknown", "No date"
    c["ca_details"] = ca_map.get(c["domain"], {})


def get_stats():
    s = {"all": collection1.count_documents({})}
    for k in ("valid", "soon", "expired"):
        s[k] = collection1.count_documents(build_filter(status=k))
    return s


def get_issuers():
    counts = {}
    for g in collection1.aggregate([{"$group": {"_id": "$issuer", "n": {"$sum": 1}}}]):
        name = field(g["_id"]) or field(g["_id"], "O")
        if name:
            counts[name] = counts.get(name, 0) + g["n"]
    return sorted(counts.items(), key=lambda x: -x[1])


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.get("/gov.in", response_class=HTMLResponse)
def certificates(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=10, le=200),
    q: str = "",
    status: str = "all",
    issuer: str = "",
    sort: str = "domain",
    order: str = "asc",
):
    sort = sort if sort in SORTS else "domain"
    order = "desc" if order == "desc" else "asc"
    flt = build_filter(q, status, issuer)

    total = collection1.count_documents(flt)
    pages = max(1, ceil(total / size))
    page = min(page, pages)

    direction = 1 if order == "asc" else -1
    sort_spec = [(SORTS[sort], direction)] + ([("domain", 1)] if sort != "domain" else [])
    certs = list(collection1.find(flt, {"_id": 0}).sort(sort_spec).skip((page - 1) * size).limit(size))

    domains = [(c.get("domain") or "").strip().lower() for c in certs]
    ca_map = {d["domain"]: d for d in collection2.find({"domain": {"$in": domains}}, {"_id": 0})}
    now = utcnow()
    for c in certs:
        decorate(c, ca_map, now)

    params = {"q": q, "status": status, "issuer": issuer, "sort": sort, "order": order, "size": size, "page": page}

    def link(**kw):
        p = {k: v for k, v in {**params, **kw}.items() if v not in ("", None, "all")}
        return "/gov.in?" + urlencode(p)

    def export_link():
        p = {k: v for k, v in {"q": q, "status": status, "issuer": issuer}.items() if v not in ("", "all")}
        return "/gov.in/export.csv?" + urlencode(p)

    return templates.TemplateResponse(request, "index2.html", {
        "request": request, "certs": certs, "total": total, "page": page, "pages": pages, "size": size,
        "q": q, "status": status, "issuer": issuer, "sort": sort, "order": order,
        "stats": get_stats(), "issuers": get_issuers(), "link": link, "export_link": export_link(),
    })


@app.get("/gov.in/export.csv")
def export_csv(q: str = "", status: str = "all", issuer: str = ""):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["domain", "issuer", "ca_id", "valid_from", "valid_to"])
    for c in collection1.find(build_filter(q, status, issuer),
                              {"_id": 0, "domain": 1, "issuer": 1, "ca_id": 1, "valid_from": 1, "valid_to": 1}).sort("domain", 1):
        w.writerow([c.get("domain"), field(c.get("issuer")), c.get("ca_id"), c.get("valid_from"), c.get("valid_to")])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=certificates.csv"})
