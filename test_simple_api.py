from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/test")
async def test_get():
    return {"message": "GET works"}

@app.post("/test")
async def test_post(data: dict):
    return {"message": "POST works", "received": data}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)