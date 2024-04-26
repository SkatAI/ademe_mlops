from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/bonjour/{name}")
async def bonjour(name:str):
    return {"message": f"Bonjour {name}"}

@app.get("/plus/")
async def plus(a: int, b: int):
    print("addition")
    return {"message": a+b}
