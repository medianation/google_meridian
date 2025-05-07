import json
import traceback

import pandas as pd
from fastapi import APIRouter, UploadFile, File, status
from fastapi.responses import JSONResponse

from app.celery_tasks.model_training import training
from app.constants import EXCEL_FORMAT, CSV_FORMAT

router = APIRouter()


@router.post(
    '/',
    tags=['GOOGLE MERIDIAN']
)
async def load_data_for_google_meridian_education(
    file: UploadFile = File(...),
    # authorization: Annotated[int, Depends(get_jwt_token)] = Header()
):
    try:
        if file.content_type == EXCEL_FORMAT:
            df = pd.read_excel(file.file)
            data = df.to_dict(orient='records')
            training.delay(data)

        elif file.content_type == CSV_FORMAT:
            df = pd.read_csv(file.file)
            data = df.to_dict(orient='records')
            training.delay(data)

        else:
            return JSONResponse('Incorrect file format (only csv/xlsx)', status_code=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(str(e), status_code=status.HTTP_400_BAD_REQUEST)
