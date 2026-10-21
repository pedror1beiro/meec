# TOMSA 2026 — Grupo 07 (v0.3)

**Multi-Robot Trajectory Replay and Coordinate Frame Visualizer** — ISEP, Mestrado em Sistemas Autónomos.

Dashboard Python/Dash para visualizar trajetórias de três robôs com sincronização temporal, vista global NED (2D/3D), vista local, controlo de reprodução, configuração YAML e exportação CSV. A implementação está repartida em módulos simples: `tomsa/data.py` (carregamento), `tomsa/coordinates.py` (matemática), `tomsa/replay.py` (tempo/referenciais) e `tomsa/figures.py` (gráficos). `app.py` contém os controlos.

## Instalação

No Windows, dentro desta pasta:

```cmd
uv venv .venv
.venv\Scripts\activate
uv pip install -r requirements.txt
python app.py
```

Abrir http://127.0.0.1:8050.

## Ficheiros de dados — não incluídos no repositório público

O ZIP original `TL2026.zip`, os seus CSV e visualizações/exportações derivadas estão **excluídos** por restrição de utilização na UC.

Para executar com dados reais, obter o ZIP original através dos materiais oficiais da UC e colocá-lo **localmente** em `data/TL2026.zip`. O `config.yaml` já aponta para esse caminho.

Para testar a interface sem ficheiros restritos, alterar `data.mode` em `config.yaml` de `zip` para `demo`; os dados sintéticos não representam os logs reais.

## Conceitos e limitações

- Cada posição dos CSV corresponde a latitude/longitude (graus) e altitude (metros), convertida para ECEF WGS84 e depois para NED comum.
- Replay por registo temporal mais próximo, com tolerância de ±0,3 s e sem interpolação.
- Na vista local, subtraímos a posição do robô central. A rotação `R(q)^T` só é aplicada para `world_ned` sob uma hipótese corpo→NED **não confirmada** pela documentação dos dados. Caso contrário, usamos NED transladado.
- O datum vertical da altitude e o significado dos quaterniões ainda precisam de confirmação.
- O export CSV de posição local indica se utilizou `robot_body_assumed` ou `ned_translated`.

## Testes

```cmd
python -m pytest -q
```

Alguns testes dependem do ZIP real no local indicado. Antes da defesa, verificar Play/Pause, 2D/3D, seleção de cada robô e exportações.

A primeira entrega (`TOMSA_TL1_GRUPO07.ipynb`) está na pasta da UC, um nível acima deste projeto.
