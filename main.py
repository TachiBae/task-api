from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="Task API", version="1.0")


# ---------- schemas ----------
class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, examples=["Buy milk"])


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, examples=["Buy oat milk"])
    done: bool | None = None


# ---------- in-memory "database" ----------
def seed_tasks():
    return [
        {"id": 1, "title": "Learn HTTP", "done": True},
        {"id": 2, "title": "Build a CRUD API", "done": False},
        {"id": 3, "title": "Publish to GitHub", "done": False},
    ]

tasks = seed_tasks()
next_id = 4

def reset_state():
    """Restore the 3 example tasks (used by tests and the optional /reset)."""
    global tasks, next_id
    tasks = seed_tasks()
    next_id = 4

def find_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---------- error handlers ----------
@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    problems = [
        f"{'.'.join(str(p) for p in e['loc'][1:]) or 'body'}: {e['msg']}"
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request", "details": problems},
    )


# ---------- housekeeping ----------
@app.get("/", summary="Describe the API")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


# ---------- CRUD ----------
@app.get("/tasks", response_model=list[Task], summary="List all tasks")
def list_tasks():
    """Return every task in the in-memory list."""
    return tasks


@app.get("/tasks/{task_id}", response_model=Task, summary="Get one task")
def get_task(task_id: int):
    """Return the task with this id, or 404 if it does not exist."""
    return find_task(task_id)


@app.post("/tasks", response_model=Task, status_code=201, summary="Create a task")
def create_task(body: TaskCreate):
    """Create a task from `{"title": "..."}`. The server sets `id` and `done=false`."""
    global next_id
    task = {"id": next_id, "title": body.title, "done": False}
    next_id += 1
    tasks.append(task)
    return task
