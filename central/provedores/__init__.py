"""Conectores das redes. Cada um sabe testar a conexão, coletar números e comentários, publicar e responder.

Todos devolvem dados no mesmo formato (ver base.py), e quem guarda é o social.py, no banco local: trocar de
provedor (do Metricool para a API direta, por exemplo) não perde nada.
"""
from . import claude, instagram, metricool, tiktok, youtube

PROVEDORES = {p.ID: p for p in (metricool.Metricool(), instagram.Instagram(), youtube.YouTube(), tiktok.TikTok(), claude.PonteClaude())}
