# TOMSA · Grupo 07 — Guião de apresentação e defesa (v0.3)

## Ideia principal (30 segundos)

Desenvolvemos uma aplicação em Python/Dash que lê os registos de três robôs e permite acompanhar as suas trajetórias numa vista global e numa vista relativa ao robô escolhido. Como os ficheiros contêm latitude/longitude, convertemos as posições para um referencial comum NED, alinhamos os registos por tempo e apresentamos os resultados em gráficos Plotly. A aplicação permite controlar a reprodução e exportar posições e configuração.

## Demonstração recomendada (5–7 minutos)

1. Mostrar o `config.yaml` e explicar os três CSV; os dados originais não são alterados.
2. Vista global 2D/3D: Norte, Este, Baixo em metros, na mesma origem.
3. Replay: Play/Pause, timestamp e amostra mais próxima com tolerância ±0,3 s.
4. Vista relativa: selecionar robô 1 e explicar a transformação de referencial; selecionar robô 7 para mostrar NED transladado (sem orientação assumida).
5. Exportar CSV global, CSV local e YAML. Verificar colunas e unidades.
6. Apresentar testes de invariância e limites conhecidos.

## Matemática

- Geodésicas (latitude, longitude, altitude) → ECEF (WGS84) → NED. NED: Norte, Este e Baixo.
- Referencial relativo sem orientação validada: `p_rel = p - p0`.
- Sob a hipótese de quaternião corpo→NED: `p_local = R(q)^T(p-p0)`. O robô central passa para [0,0,0]; rotações preservam distâncias.
- Sincronização: amostra temporal mais próxima no intervalo comum, sem interpolação.

## Perguntas prováveis

**Porquê NumPy/SciPy?** Operações vetoriais, matrizes de rotação e quaterniões.

**Porquê pandas?** Leitura/validação dos CSV.

**Porquê Dash/Plotly?** Dashboard e gráficos interativos 2D/3D, implementados em Python.

**Porquê YAML?** Configuração desacoplada do código.

**Porquê NED?** Um referencial cartesiano comum em metros, adequado para comparar posições relativas.

**As orientações estão comprovadas?** Não. `world_ned` é usado como hipótese explicitamente assinalada, e o robô 7 fica em NED transladado. Precisamos de confirmação do professor sobre a convenção dos quaterniões.

**Que limitações existem?** Datum vertical incerto, quaterniões não validados, pressuposto de relógios sincronizados e ausência de interpolação.

## Preparação entre elementos do grupo

- Dados, formatos, `config.yaml` e `data.py`.
- WGS84 → ECEF → NED, `coordinates.py`.
- Replay, Dash/Plotly, exportação e testes.

Todos devem conseguir explicar as três partes.
