"""FastAPI application — PR Reviewer Agent backend."""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from app.agent.graph import review_graph
from app.models.schemas import ReviewRequest, ReviewResult
from app.services.github import fetch_pr_diff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PR Reviewer Agent",
    version="1.0.0",
    description="AI-powered pull request reviewer using LangGraph",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/review")
async def review_pr(request: ReviewRequest):
    """Run a full PR review and return the result."""
    diff = request.diff

    if request.pr_url and not diff:
        try:
            diff = await fetch_pr_diff(request.pr_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch PR diff: {e}")

    if not diff.strip():
        raise HTTPException(status_code=400, detail="No diff provided.")

    try:
        result = await review_graph.ainvoke(
            {
                "raw_diff": diff,
                "parsed_files": [],
                "reviews": [],
                "suggested_patch": "",
                "overall_summary": "",
                "test_suggestions": "",
                "status": "",
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    return ReviewResult(
        categories=result["reviews"],
        suggested_patch=result.get("suggested_patch", ""),
        overall_summary=result.get("overall_summary", ""),
        test_suggestions=result.get("test_suggestions", ""),
    )


@app.post("/api/review/stream")
async def review_pr_stream(request: ReviewRequest):
    """Stream review progress via Server-Sent Events."""
    diff = request.diff

    if request.pr_url and not diff:
        try:
            diff = await fetch_pr_diff(request.pr_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch PR diff: {e}")

    if not diff.strip():
        raise HTTPException(status_code=400, detail="No diff provided.")

    async def event_generator():
        try:
            async for event in review_graph.astream(
                {
                    "raw_diff": diff,
                    "parsed_files": [],
                    "reviews": [],
                    "suggested_patch": "",
                    "overall_summary": "",
                    "test_suggestions": "",
                    "status": "",
                },
                stream_mode="updates",
            ):
                # Each event is a dict of {node_name: state_update}
                for node_name, update in event.items():
                    status = update.get("status", "")
                    reviews = update.get("reviews", [])

                    # Send status update
                    if status:
                        yield {"event": "status", "data": json.dumps({"node": node_name, "message": status})}

                    # Send partial review results as they arrive
                    if reviews:
                        for review in reviews:
                            yield {
                                "event": "review",
                                "data": review.model_dump_json(),
                            }

                    # Send patch if available
                    if "suggested_patch" in update and update["suggested_patch"]:
                        yield {
                            "event": "patch",
                            "data": json.dumps({"patch": update["suggested_patch"]}),
                        }

                    # Send summary if available
                    if "overall_summary" in update and update["overall_summary"]:
                        yield {
                            "event": "summary",
                            "data": json.dumps({
                                "overall_summary": update["overall_summary"],
                                "test_suggestions": update.get("test_suggestions", ""),
                            }),
                        }

            yield {"event": "done", "data": "{}"}

        except ValueError as e:
            yield {"event": "error", "data": json.dumps({"detail": str(e)})}
        except Exception as e:
            logger.exception("Stream error")
            yield {"event": "error", "data": json.dumps({"detail": str(e)})}

    return EventSourceResponse(event_generator())
