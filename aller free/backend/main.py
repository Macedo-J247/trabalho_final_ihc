# main.py (raiz do projeto)

from fastapi import FastAPI

# importa engine/Base do pacote app (sua pasta app tem database.py)
from app.database import Base, engine

# IMPORTA models ANTES de criar as tabelas
# isso garante que Base.metadata conheça todas as tabelas declaradas
import app.models  # <- garante que os modelos sejam registrados no metadata

# Cria as tabelas na inicialização (aponta para database.db definido em app/database.py)
Base.metadata.create_all(bind=engine)

# cria a app
app = FastAPI(title="IHC Marketplace - MVP")

# importa routers dos endpoints (são módulos irmãos na pasta endpoints/)
from endpoints import usuario, produto, lojista, tags

app.include_router(usuario.router)
app.include_router(produto.router)
app.include_router(lojista.router)
app.include_router(tags.router)


# rota simples pra sanity check
@app.get("/")
def ping():
    return {"ok": True, "msg": "API IHC rodando"}
