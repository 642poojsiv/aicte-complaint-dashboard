import os, uuid
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dotenv import load_dotenv
from .database import Base, engine, get_db
from .models import User, Institution, Complaint, AuditLog
from .schemas import LoginIn, ComplaintCreate, StatusUpdate
from .security import verify_password, create_token, current_user, require_roles
from .logic import route_category, similarity, ACTIVE

load_dotenv()
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Institution Complaint Monitoring API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_ORIGIN","http://localhost:3000")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def log(db, complaint, user, action, details=""):
    db.add(AuditLog(complaint_id=complaint.id, user_id=user.id, action=action, details=details))

@app.get("/api/health")
def health(): return {"status":"ok"}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user), "token_type":"bearer",
            "user":{"id":user.id,"name":user.name,"email":user.email,"role":user.role}}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id":user.id,"name":user.name,"email":user.email,"role":user.role}

def complaint_json(c):
    return {"id":c.id,"complaint_no":c.complaint_no,"permanent_id":c.institution.permanent_id,
      "institution_name":c.institution.name,"region":c.institution.region,"category":c.category,
      "subject":c.subject,"description":c.description,"complainant_name":c.complainant_name,
      "complainant_email":c.complainant_email,"assigned_cell":c.assigned_cell,"status":c.status,
      "created_at":c.created_at,"updated_at":c.updated_at,"due_at":c.due_at,
      "document_url":c.document_url}

@app.post("/api/complaints")
def create_complaint(data: ComplaintCreate, db: Session = Depends(get_db),
                      user: User = Depends(require_roles("Admin","Officer"))):
    institution = db.query(Institution).filter_by(permanent_id=data.permanent_id.strip()).first()
    if not institution:
        institution = Institution(permanent_id=data.permanent_id.strip(), name=data.institution_name.strip(), region=data.region)
        db.add(institution); db.flush()
    else:
        institution.name = data.institution_name.strip()
        if data.region: institution.region = data.region
    now = datetime.now(timezone.utc)
    days = int(os.getenv("SLA_DAYS","45"))
    complaint = Complaint(complaint_no="AICTE-"+uuid.uuid4().hex[:8].upper(),
        institution_id=institution.id, complainant_name=data.complainant_name,
        complainant_email=data.complainant_email, category=data.category, subject=data.subject,
        description=data.description, document_url=data.document_url,
        assigned_cell=route_category(data.category), status="Pending",
        created_at=now, updated_at=now, due_at=now+timedelta(days=days))
    db.add(complaint); db.flush()
    log(db, complaint, user, "Complaint filed", f"Automatically routed to {complaint.assigned_cell}")
    db.commit(); db.refresh(complaint)
    return {"complaint":complaint_json(complaint),"duplicate_check":find_duplicates(db, complaint)}

def find_duplicates(db, complaint):
    others = db.query(Complaint).filter(Complaint.id != complaint.id,
        Complaint.status.in_(ACTIVE)).all()
    matches=[]
    for old in others:
        same_id = old.institution.permanent_id == complaint.institution.permanent_id
        score = similarity(complaint.subject+" "+complaint.description,
                           old.subject+" "+old.description)
        if same_id or score >= 0.38:
            matches.append({"complaint_no":old.complaint_no,"permanent_id":old.institution.permanent_id,
                "subject":old.subject,"status":old.status,"assigned_cell":old.assigned_cell,
                "same_permanent_id":same_id,"similarity":score})
    matches.sort(key=lambda x:(not x["same_permanent_id"], -x["similarity"]))
    return matches[:10]

@app.get("/api/complaints")
def list_complaints(status: str | None = None, q: str | None = None,
                    db: Session = Depends(get_db), user: User = Depends(current_user)):
    query=db.query(Complaint).join(Institution)
    if status: query=query.filter(Complaint.status==status)
    if q:
        term=f"%{q}%"
        query=query.filter((Complaint.complaint_no.ilike(term)) |
          (Complaint.subject.ilike(term)) | (Institution.permanent_id.ilike(term)) |
          (Institution.name.ilike(term)))
    return [complaint_json(c) for c in query.order_by(desc(Complaint.created_at)).limit(500).all()]

@app.get("/api/complaints/{complaint_id}")
def get_complaint(complaint_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    c=db.get(Complaint,complaint_id)
    if not c: raise HTTPException(404,"Complaint not found")
    return complaint_json(c)

@app.get("/api/complaints/{complaint_id}/duplicates")
def duplicates(complaint_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    c=db.get(Complaint,complaint_id)
    if not c: raise HTTPException(404,"Complaint not found")
    return find_duplicates(db,c)

@app.patch("/api/complaints/{complaint_id}/status")
def update_status(complaint_id:int, data:StatusUpdate, db:Session=Depends(get_db),
                  user:User=Depends(require_roles("Admin","Officer"))):
    allowed={"Pending","Under Process","Resolved","Escalated"}
    if data.status not in allowed: raise HTTPException(400,"Unsupported status")
    c=db.get(Complaint,complaint_id)
    if not c: raise HTTPException(404,"Complaint not found")
    old=c.status; c.status=data.status; c.updated_at=datetime.now(timezone.utc)
    log(db,c,user,"Status changed",f"{old} → {data.status}. {data.comment}".strip())
    db.commit(); db.refresh(c)
    return complaint_json(c)

@app.get("/api/complaints/{complaint_id}/audit")
def audit(complaint_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    if not db.get(Complaint,complaint_id): raise HTTPException(404,"Complaint not found")
    rows=db.query(AuditLog).filter_by(complaint_id=complaint_id).order_by(AuditLog.timestamp.asc()).all()
    return [{"id":r.id,"action":r.action,"details":r.details,"timestamp":r.timestamp,
             "user_name":r.user.name} for r in rows]

@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db), user:User=Depends(current_user)):
    rows=db.query(Complaint).all()
    now=datetime.now(timezone.utc)
    counts={s:sum(1 for c in rows if c.status==s) for s in ["Pending","Under Process","Resolved","Escalated"]}
    by_cell={}
    by_category={}
    sla=[]
    for c in rows:
        by_cell[c.assigned_cell]=by_cell.get(c.assigned_cell,0)+1
        by_category[c.category]=by_category.get(c.category,0)+1
        due=c.due_at
        if due.tzinfo is None: due=due.replace(tzinfo=timezone.utc)
        if c.status!="Resolved":
            remaining=(due-now).total_seconds()
            if remaining <= 7*86400:
                sla.append({"complaint_no":c.complaint_no,"subject":c.subject,"status":c.status,
                  "due_at":c.due_at,"days_remaining":round(remaining/86400,1),
                  "breached":remaining<0})
    return {"total":len(rows),"counts":counts,"by_cell":by_cell,"by_category":by_category,
            "sla_alerts":sorted(sla,key=lambda x:x["days_remaining"])}
