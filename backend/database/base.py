from __future__ import annotations
from datetime import datetime
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel
from bson import ObjectId

class AppBaseModel(BaseModel):
    """
    AppBaseModel (Base Configuration Model)

    Purpose:
    --------
    Provides a shared configuration for all Pydantic models in the application.

    This ensures consistent behavior across all schemas such as:
    - JSON serialization
    - Handling MongoDB ObjectId
    - Field population behavior

    Configuration:
    --------------
    populate_by_name : bool
        Allows fields to be populated using aliases (e.g., '_id'  'id').

    arbitrary_types_allowed : bool
        Allows usage of non-standard types like ObjectId.

    json_encoders : dict
        Custom serialization rules:
        - datetime  ISO format string
        - ObjectId  string

    Behavior:
    ---------
    - Ensures all derived models automatically inherit these settings.
    - Simplifies API responses and JSON conversion.

    Edge Cases:
    -----------
    - Incorrect ObjectId handling without this config may cause serialization errors.
    - datetime fields are always returned in ISO format (important for frontend).
    """
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            ObjectId: str,
        },
    }


T = TypeVar("T")


class SuccessResponse(AppBaseModel, Generic[T]):
    """
    SuccessResponse Generic Schema

    Purpose:
    --------
    Standardized response format for successful API responses.

    This ensures consistency across all endpoints.

    Fields:
    -------
    success : bool
        Indicates success status (always True).

    data : Optional[T]
        The actual response payload (generic type).

    message : Optional[str]
        Optional message describing the success.

    Behavior:
    ---------
    - Can wrap any type of data using generics.
    - Used in API responses for uniform structure.

    Example:
    --------
    return SuccessResponse(data=user_data, message="User created successfully")

    Edge Cases:
    -----------
    - data can be None if no payload is required.
    - message is optional.
    """
    success: bool = True
    data:    Optional[T] = None
    message: Optional[str] = None


class ErrorResponse(AppBaseModel):
    """
    ErrorResponse Schema

    Purpose:
    --------
    Standardized response format for API errors.

    Provides a consistent way to return error information to clients.

    Fields:
    -------
    success : bool
        Indicates failure status (always False).

    error : str
        Short error message.

    detail : Optional[str]
        Additional details about the error.

    Behavior:
    ---------
    - Used across APIs to standardize error handling.
    - Helps frontend handle errors consistently.

    Example:
    --------
    return ErrorResponse(error="Invalid input", detail="Email is required")

    Edge Cases:
    -----------
    - 'error' field is mandatory.
    - 'detail' is optional but recommended for debugging.
    """
     
    success: bool = False
    error:   str
    detail:  Optional[str] = None
