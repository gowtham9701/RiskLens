"""Portfolio Builder (optimiser) routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import OptimisationRun, User
from ...schemas import BuilderIn
from ...services import optimiser_service
from ..deps import get_current_user

router = APIRouter(prefix="/portfolio-builder", tags=["portfolio-builder"])


@router.post("/generate")
def generate(body: BuilderIn, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    result = optimiser_service.generate(
        db,
        amount=body.amount,
        objective=body.objective,
        constraints=body.constraints.model_dump(),
        universe=body.universe,
    )
    run = OptimisationRun(
        user_id=user.id, objective=body.objective, amount=body.amount,
        inputs_json=body.model_dump(), feasible=result["feasible"],
        result_json={"allocations": result["allocations"],
                     "expected_yield": result["expected_yield"]},
    )
    db.add(run)
    db.commit()
    result["run_id"] = run.id
    return result


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    run = db.get(OptimisationRun, run_id)
    if not run or run.user_id != user.id:
        from fastapi import HTTPException
        raise HTTPException(404, "Run not found")
    return {"id": run.id, "objective": run.objective, "amount": float(run.amount),
            "feasible": run.feasible, "result": run.result_json, "inputs": run.inputs_json}
