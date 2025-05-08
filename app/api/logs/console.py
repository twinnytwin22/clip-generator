from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

router = APIRouter()
log_lines = []

class InMemoryLogHandler(logging.Handler):
    def emit(self, record):
        log_lines.append(self.format(record))
        # Limit to last 100 lines
        if len(log_lines) > 100:
            del log_lines[0]

log_handler = InMemoryLogHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
console = logging.getLogger("console")
console.addHandler(log_handler)

@router.get("/logs")
async def get_logs():
    return JSONResponse(content={"logs": "\n".join(log_lines[-20:])})
