from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from .. import schemas
from ..models import AnalysisTask
from ..tasks import analyze_batch_stocks, scan_market_opportunities
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/batch-analysis", response_model=schemas.BaseResponse)
async def create_batch_analysis_task(
    request: schemas.BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建批量分析任务"""
    try:
        if len(request.symbols) > 50:
            raise HTTPException(status_code=400, detail="单次最多分析50只股票")
        
        # 创建任务记录
        task_id = str(uuid.uuid4())
        task = AnalysisTask(
            task_id=task_id,
            task_type="batch_stocks",
            symbols=request.symbols,
            status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # 提交后台任务
        background_tasks.add_task(
            analyze_batch_stocks.delay,
            task_id,
            request.symbols,
            request.analysis_types,
            request.priority
        )
        
        return schemas.BaseResponse(
            message="批量分析任务已创建",
            data={
                "task_id": task_id,
                "symbols": request.symbols,
                "status": "pending"
            }
        )
        
    except Exception as e:
        logger.error(f"创建批量分析任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-scan", response_model=schemas.BaseResponse)
async def create_market_scan_task(
    background_tasks: BackgroundTasks,
    sector: Optional[str] = None,
    market_cap_min: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """创建市场扫描任务"""
    try:
        # 创建任务记录
        task_id = str(uuid.uuid4())
        task = AnalysisTask(
            task_id=task_id,
            task_type="market_scan",
            symbols=[],  # 市场扫描不需要预定义股票列表
            status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # 提交后台任务
        background_tasks.add_task(
            scan_market_opportunities.delay,
            task_id,
            sector,
            market_cap_min
        )
        
        return schemas.BaseResponse(
            message="市场扫描任务已创建",
            data={
                "task_id": task_id,
                "scan_criteria": {
                    "sector": sector,
                    "market_cap_min": market_cap_min
                },
                "status": "pending"
            }
        )
        
    except Exception as e:
        logger.error(f"创建市场扫描任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}", response_model=schemas.BaseResponse)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """获取任务状态"""
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return schemas.BaseResponse(
            data={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "symbols": task.symbols,
                "status": task.status,
                "progress": task.progress,
                "result": task.result,
                "error_message": task.error_message,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
        )
        
    except Exception as e:
        logger.error(f"获取任务状态失败 {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=schemas.BaseResponse)
async def get_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    try:
        query = db.query(AnalysisTask)
        
        if status:
            query = query.filter(AnalysisTask.status == status)
        
        if task_type:
            query = query.filter(AnalysisTask.task_type == task_type)
        
        tasks = query.order_by(AnalysisTask.created_at.desc()).limit(limit).all()
        
        result = []
        for task in tasks:
            result.append({
                "task_id": task.task_id,
                "task_type": task.task_type,
                "symbols_count": len(task.symbols),
                "status": task.status,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })
        
        return schemas.BaseResponse(data=result)
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}", response_model=schemas.BaseResponse)
async def cancel_task(task_id: str, db: Session = Depends(get_db)):
    """取消任务"""
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="任务已完成，无法取消")
        
        # 更新任务状态
        task.status = "cancelled"
        task.completed_at = datetime.now()
        db.commit()
        
        # TODO: 实际取消Celery任务
        
        return schemas.BaseResponse(
            message="任务已取消",
            data={"task_id": task_id, "status": "cancelled"}
        )
        
    except Exception as e:
        logger.error(f"取消任务失败 {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))