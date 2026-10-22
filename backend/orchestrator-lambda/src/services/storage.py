"""
Storage for client data, peer data and generated reports.

STORAGE_BACKEND selects the implementation; both expose the same functions:
- local: folders under LOCAL_DATA_DIR (services/local_storage.py)
- s3:    Amazon S3 buckets (services/s3_service.py)
"""
from src.config.settings import STORAGE_BACKEND

if STORAGE_BACKEND == "s3":
    from src.services.s3_service import (  # noqa: F401
        fetch_files_with_metadata,
        list_json_files,
        read_file,
        read_json,
        read_json_metadata,
        read_pdf,
        save_json,
    )
elif STORAGE_BACKEND == "local":
    from src.services.local_storage import (  # noqa: F401
        fetch_files_with_metadata,
        list_json_files,
        read_file,
        read_json,
        read_json_metadata,
        read_pdf,
        save_json,
    )
else:
    raise ValueError(f"Unknown STORAGE_BACKEND '{STORAGE_BACKEND}'. Use 'local' or 's3'.")
