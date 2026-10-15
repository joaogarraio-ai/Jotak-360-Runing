"""Uso: python -m afiliados_ml [--db afiliados.db] [--porta 8000]"""
import argparse

from .web import servir

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--db", default="afiliados.db")
ap.add_argument("--porta", type=int, default=8000)
a = ap.parse_args()
servir(a.db, a.porta)
