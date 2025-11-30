# TODO: Add Auth Router and Frontend Integration

## Backend Changes
- [x] Edit `backend/app/schemas/auth.py`: Add RegisterRequest and RegisterResponse models, import EmailStr.
- [x] Edit `backend/app/routers/auth.py`: Change prefix to "/auth", add register endpoint with RegisterRequest/RegisterResponse.

## Frontend Changes
- [x] Edit `frontend/src/services/auth.ts`: Update registerRequest payload to {email, password, full_name}, response to {message}.
- [x] Edit `frontend/vite.config.ts`: Add proxy for "/api" to "http://localhost:8000".

## Testing
- [x] Restart backend with uvicorn.
- [x] Test register endpoint in Swagger.
- [x] Test frontend register call (backend API tested successfully).

## Additional Fixes
- [x] Update register endpoint to create actual users in DB.
- [x] Create user Mohith with provided details.
