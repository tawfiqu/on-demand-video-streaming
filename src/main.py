from typing import Annotated
from fastapi import FastAPI, Path, Request, Response
from upload_service import upload_video
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import secrets
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()

security = HTTPBasic()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    """
        To be replaced by database.
    """
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"test"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"test"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/health")
@limiter.limit("5/minute")
def test(request: Request):
    return "healthy"

@app.post("/upload")
@limiter.limit("5/minute")
def upload(request: Request, video_source_path:str):
    upload_video(video_source_path)
    return JSONResponse(content={"status": "completed"}, status_code=201)

@app.get("/video.mpd")
@limiter.limit("5/minute")
def serve_mpd(request: Request, username: Annotated[str, Depends(get_current_username)]):
    with open('media/dash.mpd', 'r') as file:
        data = file.read()
    return Response(content=data, media_type="application/xml")

@app.get('/{segment}')
def video_segment(request: Request, segment: Annotated[str, Path(title="The ID of the item to get")], username: Annotated[str, Depends(get_current_username)]):
    def iterfile():
        with open(f"media/{segment}", mode='rb') as f:
            yield from f

    return StreamingResponse(iterfile(), media_type='video/mp4')

if __name__=="__main__":
    uvicorn.run("main:app",host='0.0.0.0', reload=True, port=8080)
