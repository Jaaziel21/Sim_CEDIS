#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

# Nombre por defecto del archivo editable
DEFAULT_CONFIG_PATH = "sim_config.json"

DEFAULTS_BASE: Dict[str, Dict[str, Any]] = {
    "global": {
        "escenario": "seed42",
    },

    "generador_layout": {
        "seed": 67,
        "ancho": 700,
        "alto": 300,
        "estaciones": 10,

        # overrides opcionales de salida
        "salida_layout": None,
        "salida_estaciones": None,
        "salida_anaqueles": None,
        "salida_spawn": None,

        # compatibilidad vieja
        "prefijo": None,
    },

    "generador_pedidos": {
        "seed": 67,
        "pedidos": 600,
        "burst": False,

        # overrides opcionales
        "archivo_estaciones": None,
        "archivo_anaqueles": None,
        "salida": None,
    },

    "demo_final": {
        "seed": 67,
        "robots": 20,
        "ticks": 10000,

        # overrides de entradas
        "layout": None,
        "estaciones": None,
        "anaqueles": None,
        "spawn": None,
        "pedidos": None,

        # salida
        "salida_metricas": None,
    },

    "visualiza_simulacion": {
        "seed": 67,
        "robots": 20,
        "ticks": 10000,
        "pasos_por_frame": 25,
        "fps": 20,

        
        "ffmpeg_path": None,

        "normalizar_pedidos": False,

        "layout": None,
        "estaciones": None,
        "anaqueles": None,
        "spawn": None,
        "pedidos": None,

        "layout_png": None,
        "salida_video": None,
        "prefijo_heatmap": None,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:

    out = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def cargar_config(path: Optional[str]) -> Dict[str, Any]:
    """
    Carga config desde JSON y hace merge con DEFAULTS_BASE.

    """
    cfg = deepcopy(DEFAULTS_BASE)

    if not path:
        return cfg

    p = Path(path)
    if not p.exists():
        print(f"Advertencia: archivo de configuración no existe: {path}")
        return cfg

    with p.open("r", encoding="utf-8") as f:
        user_cfg = json.load(f)

    if not isinstance(user_cfg, dict):
        raise ValueError("El archivo de configuración debe contener un objeto JSON en el nivel raíz.")

    cfg = _deep_merge(cfg, user_cfg)
    return cfg


def agregar_argumento_config(
    parser: argparse.ArgumentParser,
    default_path: str = DEFAULT_CONFIG_PATH,
) -> None:

    ya_existe = any("--config" in action.option_strings for action in parser._actions)
    if ya_existe:
        return

    parser.add_argument(
        "--config",
        type=str,
        default=default_path,
        help=f"Ruta al JSON de configuración (default: {default_path}).",
    )


def _filtrar_claves_para_parser(
    parser: argparse.ArgumentParser,
    defaults: Dict[str, Any],
) -> Dict[str, Any]:

    dests_validos = {a.dest for a in parser._actions}
    return {k: v for k, v in defaults.items() if k in dests_validos}


def aplicar_defaults_desde_config(
    parser: argparse.ArgumentParser,
    script_key: str,
    argv: Optional[list[str]] = None,
) -> Dict[str, Any]:

    agregar_argumento_config(parser)

    args_parciales, _ = parser.parse_known_args(argv)
    ruta_cfg = getattr(args_parciales, "config", DEFAULT_CONFIG_PATH)

    cfg = cargar_config(ruta_cfg)

    defaults_globales = cfg.get("global", {})
    defaults_script = cfg.get(script_key, {})

    if not isinstance(defaults_globales, dict):
        raise ValueError("La sección 'global' del config debe ser un objeto JSON.")
    if not isinstance(defaults_script, dict):
        raise ValueError(f"La sección '{script_key}' del config debe ser un objeto JSON.")

    defaults_finales = {}
    defaults_finales.update(defaults_globales)
    defaults_finales.update(defaults_script)

    defaults_filtrados = _filtrar_claves_para_parser(parser, defaults_finales)
    parser.set_defaults(**defaults_filtrados)

    return cfg