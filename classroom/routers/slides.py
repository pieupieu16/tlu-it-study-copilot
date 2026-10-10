"""Slide deck management, PPTX/PDF ingestion, and checkpoint attachment.

Target module: tlu_study_assistant_web.classroom.routers.slides
"""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..config import get_settings
from ..database import get_db
from ..models import Checkpoint, Course, Question, Session, Slide, User
from ..services import llm
from ..services.slide_import import page_image_url, parse_pdf, parse_pptx, slide_plain_text
from ..schemas import (
    CheckpointCreate,
    CheckpointOut,
    DraftRequest,
    DraftResponse,
    QuestionIn,
    QuestionOut,
    SlideOut,
    SlideUpdate,
)
from ..security import current_user

settings = get_settings()
router = APIRouter(tags=["Classroom Slides"])
MAX_UPLOAD_BYTES = 40 * 1024 * 1024


def _owned_course(db: DbSession, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if course is None or course.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoá học.")
    return course


def _owned_slide(db: DbSession, slide_id: int, user: User) -> Slide:
    slide = db.get(Slide, slide_id)
    if slide is None or slide.course.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy slide.")
    return slide


def _slide_out(s: Slide) -> SlideOut:
    cp = s.checkpoint
    return SlideOut(
        id=s.id,
        course_id=s.course_id,
        index=s.index,
        title=s.title,
        blocks=s.blocks or [],
        notes=s.notes or "",
        source=s.source,
        page_image=page_image_url(s.page_image),
        has_checkpoint=cp is not None,
        checkpoint_active=cp.active if cp else False,
        checkpoint_question_count=len(cp.questions) if cp else 0,
    )


def _checkpoint_out(cp: Checkpoint) -> CheckpointOut:
    return CheckpointOut(
        id=cp.id,
        slide_id=cp.slide_id,
        slide_index=cp.slide.index,
        label=cp.label,
        goal=cp.goal,
        active=cp.active,
        created_at=cp.created_at,
        questions=[
            QuestionOut(
                id=q.id,
                position=q.position,
                type=q.type,
                prompt=q.prompt,
                options=q.options,
                answer=q.answer,
                origin=q.origin,
            )
            for q in cp.questions
        ],
    )


@router.get("/deck/{course_id}", response_model=list[SlideOut])
def list_course_slides(
    course_id: int, db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> list[SlideOut]:
    """Danh sách slide trong bộ slide của một khoá học."""
    course = _owned_course(db, course_id, user)
    return [_slide_out(s) for s in course.slides]


@router.post("/deck/{course_id}/upload-pdf", response_model=list[SlideOut], status_code=201)
async def upload_pdf_deck(
    course_id: int,
    file: UploadFile = File(...),
    replace: bool = True,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> list[SlideOut]:
    """Tải lên slide bài giảng PDF thật và trích xuất thành danh sách slide."""
    course = _owned_course(db, course_id, user)
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Chỉ nhận file .pdf.")

    dest = settings.upload_dir / f"course-{course.id}-{uuid.uuid4().hex[:8]}.pdf"
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 512):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File vượt quá 40 MB.")
                out.write(chunk)
    finally:
        await file.close()

    try:
        parsed = parse_pdf(dest, page_image_dir=settings.slide_page_dir)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        reason = str(exc).strip() or type(exc).__name__
        raise HTTPException(status_code=422, detail=f"Không đọc được file PDF: {reason}") from exc

    if not parsed:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="File không có trang PDF nào.")

    if replace:
        for old in list(course.slides):
            db.delete(old)
        db.flush()
        offset = 0
    else:
        offset = len(course.slides)

    created: list[Slide] = []
    for item in parsed:
        slide = Slide(
            course_id=course.id,
            index=offset + item["index"],
            title=item["title"],
            blocks=item["blocks"],
            notes=item["notes"],
            source="pdf",
            page_image=item.get("page_image", ""),
        )
        db.add(slide)
        created.append(slide)
    db.commit()
    return [_slide_out(s) for s in created]


@router.post("/deck/{course_id}/upload-pptx", response_model=list[SlideOut], status_code=201)
async def upload_pptx_deck(
    course_id: int,
    file: UploadFile = File(...),
    replace: bool = True,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> list[SlideOut]:
    """Tải lên bài giảng PPTX và đọc nội dung slide."""
    course = _owned_course(db, course_id, user)
    filename = (file.filename or "").lower()
    if not filename.endswith(".pptx"):
        raise HTTPException(status_code=415, detail="Chỉ nhận file .pptx.")

    dest = settings.upload_dir / f"course-{course.id}-{uuid.uuid4().hex[:8]}.pptx"
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 512):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File vượt quá 40 MB.")
                out.write(chunk)
        parsed = parse_pptx(dest)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Không đọc được file PPTX: {type(exc).__name__}") from exc
    finally:
        await file.close()

    if not parsed:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="File không có slide nào.")

    if replace:
        for old in list(course.slides):
            db.delete(old)
        db.flush()
        offset = 0
    else:
        offset = len(course.slides)

    created: list[Slide] = []
    for item in parsed:
        slide = Slide(
            course_id=course.id,
            index=offset + item["index"],
            title=item["title"],
            blocks=item["blocks"],
            notes=item["notes"],
            source="pptx",
        )
        db.add(slide)
        created.append(slide)
    db.commit()
    return [_slide_out(s) for s in created]


@router.get("/item/{slide_id}", response_model=SlideOut)
@router.get("/{slide_id}", response_model=SlideOut, include_in_schema=False)
def get_slide(
    slide_id: int, db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> SlideOut:
    """Xem thông tin chi tiết của một slide."""
    slide = _owned_slide(db, slide_id, user)
    return _slide_out(slide)


@router.patch("/item/{slide_id}", response_model=SlideOut)
@router.patch("/{slide_id}", response_model=SlideOut, include_in_schema=False)
def update_slide(
    slide_id: int,
    payload: SlideUpdate,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> SlideOut:
    """Cập nhật tiêu đề, ghi chú hoặc layout blocks của slide."""
    slide = _owned_slide(db, slide_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(slide, field, value)
    db.commit()
    return _slide_out(slide)


@router.post("/item/{slide_id}/checkpoint", response_model=CheckpointOut, status_code=201)
def create_checkpoint(
    slide_id: int,
    payload: CheckpointCreate,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> CheckpointOut:
    """Gắn checkpoint kiểm tra vào một slide."""
    slide = _owned_slide(db, slide_id, user)
    if slide.checkpoint is not None:
        raise HTTPException(status_code=409, detail="Slide này đã có checkpoint.")
    cp = Checkpoint(
        slide_id=slide.id,
        label=payload.label.strip() or f"Checkpoint slide {slide.index + 1}",
        goal=payload.goal.strip(),
    )
    db.add(cp)
    db.commit()
    return _checkpoint_out(cp)


@router.post("/item/{slide_id}/draft-checkpoint", response_model=DraftResponse)
def draft_checkpoint_questions(
    slide_id: int,
    payload: DraftRequest,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> DraftResponse:
    """Soạn nháp câu hỏi checkpoint bằng AI dựa trên nội dung slide."""
    slide = _owned_slide(db, slide_id, user)
    goal = slide.checkpoint.goal if slide.checkpoint else ""
    result = llm.draft_checkpoint_questions(
        slide.title, slide_plain_text(slide), goal, payload.count
    )
    if result is None:
        return DraftResponse(
            questions=[],
            source="unavailable",
            note="Không gọi được AI soạn đề hoặc AI chưa được cấu hình.",
        )
    return DraftResponse(
        questions=[QuestionIn(**q, origin="llm") for q in result["questions"]],
        source="llm",
        note=result.get("note", ""),
    )


@router.get("/session/{session_id}", response_model=list[SlideOut])
def get_session_slides(
    session_id: int, db: DbSession = Depends(get_db)
) -> list[SlideOut]:
    """Lấy danh sách slide phục vụ cho buổi học đang diễn ra."""
    session = db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy buổi học.")
    slides = db.scalars(
        select(Slide).where(Slide.course_id == session.room.course_id).order_by(Slide.index)
    ).all()
    return [_slide_out(s) for s in slides]
