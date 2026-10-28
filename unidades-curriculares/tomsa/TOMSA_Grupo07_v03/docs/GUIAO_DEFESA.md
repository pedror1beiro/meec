# TOMSA · Grupo 07 — Guião de apresentação e defesa (v0.4)

## Ideia principal (30 segundos)

Desenvolvemos uma aplicação em Python/Dash que lê os registos de três robôs e permite acompanhar as suas trajetórias num mapa, numa vista NED global e numa vista relativa ao robô escolhido. Convertemos latitude/longitude/altitude para um referencial comum, alinhamos os registos por tempo e mostramos rapidez e a sua derivada. Um painel interativo permite inspecionar a transformação rígida e verificar os seus invariantes nas próprias amostras da missão. As hipóteses físicas permanecem identificadas.

## Demonstração recomendada (5–7 minutos)

1. Mostrar o `config.yaml` e explicar os três CSV; os dados originais não são alterados.
2. Mapa: latitude/longitude originais, rasto recente e seleção do robô. Alternar percurso completo/60 s. Mostrar 3D e explicar que as ondas, ícones e pulso são ilustrativos. O círculo horizontal é aproximado; o filtro local usa distância NED 3D.
3. Replay: Play/Pause, timestamp e amostra mais próxima com tolerância ±0,3 s. A câmara do mapa não salta ao mudar o instante.
4. Vistas global/local: Norte, Este, Baixo em metros, na mesma origem. Selecionar robô 1 e explicar a hipótese de orientação; selecionar robô 7 para mostrar NED transladado.
5. Abrir **Mostrar a matemática**. Inspecionar `T` e a inversa, as duas vistas 3D, distâncias entre pares e erros numéricos. Avançar o slider e trocar o centro: as coordenadas mudam, mas as distâncias do mesmo snapshot são preservadas. Verificar os offsets temporais na tabela. Uma projeção 2D pode mudar de forma sem violar a invariância espacial.
6. Rapidez/aceleração: distinguir `d‖v‖/dt`, assinada, de `‖dv_NED/dt‖`. A segunda permanece indisponível nos logs reais sem confirmação da base. Não confundir abrandamento com aceleração total negativa.
7. Exportar CSV global, CSV local e YAML. Verificar colunas, unidades e identificação do referencial. Apresentar testes e limites conhecidos.

## Matemática

- Geodésicas (latitude, longitude, altitude) → ECEF (WGS84) → NED. NED: Norte, Este e Baixo.
- Referencial relativo sem orientação validada: `p_rel = p - p0`.
- Sob a hipótese de quaternião corpo→NED: `p_local = R(q)^T(p-p0)`. O robô central passa para [0,0,0]; rotações preservam distâncias.
- Transformação homogénea: `T_NED←local = [R, p0; 0, 1]`; inversa `[Rᵀ, −Rᵀp0; 0, 1]`. Verificar `RᵀR ≈ I`, `det R ≈ +1`, reconstrução e distâncias 3D. Usam-se valores completos, antes do arredondamento de apresentação.
- Sincronização: amostra temporal mais próxima no intervalo comum, sem interpolação.
- Rapidez: `s = ‖v‖`, invariante sob rotações ortonormais com unidades iguais. `ds/dt` é tangencial quando `s ≠ 0`; numa curva a rapidez constante pode ser zero com aceleração total não nula.
- Diferenciação: tempos reais não uniformes, separação em lacunas >2 s por defeito, sem suavização arbitrária. Para velocidade corporal confirmada, primeiro rodar para NED fixo e só depois derivar.

## Perguntas prováveis

**Porquê NumPy/SciPy?** Operações vetoriais, matrizes de rotação e quaterniões.

**Porquê pandas?** Leitura/validação dos CSV.

**Porquê Dash/Plotly?** Dashboard e gráficos interativos 2D/3D, implementados em Python.

**Porquê YAML?** Configuração desacoplada do código.

**Porquê NED?** Um referencial cartesiano comum em metros, adequado para comparar posições relativas.

**As orientações estão comprovadas?** Não. `world_ned` é usado como hipótese explicitamente assinalada, e o robô 7 fica em NED transladado. Precisamos de confirmação do professor sobre a convenção dos quaterniões.

**Se as distâncias coincidem, isso valida o quaternião?** Valida a invariância da transformação implementada. Qualquer rotação própria preserva distâncias, mesmo que não represente o sentido físico do quaternion do produtor. A confirmação exige documentação externa. As setas no mapa e a aceleração vetorial continuam bloqueadas sem essa confirmação.

**O triângulo parece diferente nas duas vistas?** As distâncias são espaciais, em 3D. A projeção das câmaras pode mudar a aparência. As duas cenas usam a mesma escala métrica nos três eixos, e a tabela permite comparar numericamente.

**Os três pontos correspondem ao mesmo instante exato?** São as amostras mais próximas do instante do replay, dentro da tolerância. A tabela mostra o desvio de cada timestamp; não se inventam pontos por interpolação.

**O círculo e o rasto acrescentam dados medidos?** O rasto liga amostras originais e omite lacunas grandes. O círculo é uma ajuda cartográfica horizontal aproximada; o brilho, os ícones e as ondas são apresentação. Nenhum desses efeitos altera os logs, a matemática ou as exportações.

**Que limitações existem?** Datum vertical incerto, quaterniões não validados, pressuposto de relógios sincronizados e ausência de interpolação.

## Preparação entre elementos do grupo

- Dados, formatos, `config.yaml` e `data.py`.
- WGS84 → ECEF → NED, `coordinates.py`.
- Replay, Dash/Plotly, exportação e testes.

Todos devem conseguir explicar as três partes.
