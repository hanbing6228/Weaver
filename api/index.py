"""
Vercel serverless entry — exports the FastAPI ASGI app.
https://vercel.com/docs/functions/runtimes/python
"""

from weaver.api.main import app

__all__ = ["app"]
