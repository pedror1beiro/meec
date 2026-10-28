# TOMSA 2026 — Grupo 07 (v0.4)

**Multi-Robot Trajectory Replay and Coordinate Frame Visualizer** — ISEP, Mestrado em Sistemas Autónomos.

Dashboard Python/Dash para os robôs 1, 4 e 7: mapa geográfico MapLibre/OpenStreetMap com camada OpenSeaMap, vistas NED 2D/3D e local, replay sincronizado, rapidez, análise de aceleração, orientação, configuração YAML e exportações CSV.

## Executar

No Windows, dentro desta pasta (o nome `TOMSA_Grupo07_v03` mantém-se para preservar os caminhos existentes):

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Abrir http://127.0.0.1:8050. O servidor escuta apenas na máquina local. Para experimentar **sem os dados restritos**, usar:

```cmd
python app.py --demo
```

A demo contém dados sintéticos, identificados na interface; não representa a missão real. Pode também definir `data.mode: demo` no YAML. Outra configuração: `python app.py --config caminho/config.yaml`; caminhos de dados relativos são resolvidos a partir da pasta desse YAML. `--demo` sobrepõe apenas o modo, sem alterar o ficheiro. A exportação YAML inclui a configuração efetiva da sessão.

São mantidas as dependências Python existentes; a atualização parcial dos gráficos requer Dash ≥ 2.17. MapLibre GL JS **5.6.1** (JS e CSS) é carregado do CDN UNPKG, sem Node/npm, framework frontend ou serviço adicional. O mapa requer WebGL e acesso à Internet ao CDN/provedores. As vistas cartesianas continuam disponíveis se o mapa falhar. Node é opcional, apenas para os testes JavaScript.

## Dados restritos — não publicar

Obter `TL2026.zip` nos materiais oficiais da UC e colocá-lo **localmente** em `data/TL2026.zip`. O ZIP contém os três CSV e `TOMSA2026_TL_readme.pdf`, que documenta a estrutura. O uso dos dados é restrito à UC TOMSA.

O ZIP, CSV, pasta `data/`, exportações e pré-visualizações geográficas derivadas não devem entrar no repositório público. Os testes novos usam dados sintéticos; testes dos dados reais são opcionais quando o ZIP está ausente. Não guardar capturas/HTML do mapa real em pastas versionadas.

## Utilização

1. Escolher o robô de referência, ajustar a proximidade e usar Play/Pause ou o slider temporal.
2. Explorar o mapa: arrastar para mover, roda/botões para zoom e botão direito + arrastar para rodar/inclinar. Em touch, usar dois dedos. **3D · oceano** inclina a câmara e ativa ondas com iluminação/reflexos ilustrativos; **Enquadrar missão** repõe o enquadramento. A câmara mantém-se durante replay e seleção do robô.
3. A camada OpenSeaMap pode ser desligada. Em **Percurso**, escolher o rasto dos últimos 30/60 s (60 s por defeito), trajetórias completas ou sem linhas. Os rastos usam apenas segmentos entre amostras originais até à amostra visível, sem interpolação nem ligação através de lacunas superiores a `kinematics.max_gap_seconds`. A idade controla o brilho, sem alterar posições. Amostras fora da tolerância não são apresentadas como posições atuais.
4. Os ícones e o anel podem ser desligados. Os ícones são pictogramas frontais ilustrativos; não indicam uma orientação física desconhecida. A seta de rumo mantém a exigência de confirmação. O contorno do marcador identifica o robô de referência; o pulso é decorativo e respeita redução de movimento. O círculo geográfico usa uma aproximação esférica horizontal (raio médio terrestre de 6 371 008,8 m) do raio escolhido. **Não é o filtro local**, que usa a norma NED 3D, nem uma medição de alcance de sensores.
5. Comparar as vistas global/local e os gráficos de rapidez/aceleração. O cursor vertical é comum ao replay; os valores atuais são calculados na amostra temporal escolhida para cada robô. Abrir **Mostrar a matemática** para inspecionar as matrizes, coordenadas, distâncias 3D e erros numéricos dessas mesmas amostras.
6. Consultar AER e exportar NED/CSV, snapshot local/CSV ou configuração/YAML no fim da página. A exportação NED mantém as colunas de posição e acrescenta rapidez, derivada da rapidez, magnitude da aceleração NED (quando válida), `child_frame_id_log` e estado de confirmação do referencial de velocidade. Valores indisponíveis ficam vazios.

O modo 3D do mapa usa **perspetiva com um material de água animado**, sem terreno, batimetria ou altitude do veículo. O sombreado de normais produz a aparência de relevo/reflexos nas ondas; a geometria do mapa continua plana. As ondas são ilustrativas, não alturas, períodos ou estado do mar medidos. A vista cartesiana NED 3D continua a mostrar a componente Down dos logs.

O efeito é recortado por polígonos `water` com `class: ocean` do esquema [OpenMapTiles](https://github.com/openmaptiles/openmaptiles/blob/master/layers/water/water.yaml), servidos por [OpenFreeMap](https://openfreemap.org/quick_start/), evitando aplicar ondas sobre terra por inferência da cor azul. A camada fica abaixo de OpenSeaMap e das trajetórias. Os limites cartográficos podem ter generalização/datas diferentes da base raster. O mapa pede apenas os mosaicos da vista atual, a partir de `map.ocean_tiles_url`; não descarrega um dataset mundial. Se o provedor falhar, mantém a base plana e indica a falha. `map.ocean_surface: false` desativa o efeito.

`assets/ocean.js` gera localmente uma textura periódica de 128×128 px com sombreado de normais, luz difusa e brilho especular, através de uma [imagem dinâmica MapLibre](https://maplibre.org/maplibre-gl-js/docs/examples/add-an-animated-icon-to-the-map/) usada como `fill-pattern`. Não há outra biblioteca 3D. Atualiza no máximo 10 vezes/s, respeita redução de movimento e para quando se seleciona 2D, se oculta a página ou se remove o mapa. A animação usa tempo visual independente do replay; não representa a evolução física do mar durante a missão nem altera posições, altitudes, velocidades ou exportações.

## Interpretação dos logs e matemática

### Posição e tempo

O README original define `pose.pose.position.x/y` como latitude/longitude em graus e `.z` como altitude em metros. Usamos geodésicas → ECEF WGS84 → NED comum, com a origem do YAML. O datum vertical da altitude (descrita como acima do nível do mar) não está confirmado como elipsoidal; a conversão ECEF mantém a hipótese de alturas comparáveis da versão anterior. Isto limita a interpretação vertical.

O replay usa `header.stamp.secs/nsecs`, preservando nanossegundos inteiros, e escolhe a amostra mais próxima dentro de ±0,3 s, sem interpolação. O intervalo comum dos três robôs define o slider. Pressupõe-se que os relógios são comparáveis. Os registos são ordenados; timestamps duplicados são rejeitados, assim como quaterniões de norma zero. Campos opcionais de velocidade inválidos não eliminam poses válidas.

### Velocidade

Os CSV têm `twist.twist.linear.{x,y,z}` e `twist.twist.angular.{x,y,z}`. O README descreve as unidades como **normalmente m/s e rad/s**, sem garantir a base das componentes. `header.frame_id` é `world_ned` nos robôs 1/4 e `WGS84` no robô 7; todos têm `child_frame_id: body`. A mensagem [ROS Odometry](https://github.com/ros/common_msgs/blob/noetic-devel/nav_msgs/msg/Odometry.msg) especifica twist em `child_frame_id`, mas o formato ROS-like destes logs não comprova que o produtor seguiu essa convenção.

Por isso, a interpretação SI usual é declarada na interface e `kinematics.confirmed_velocity_frame` começa em `unknown`. A rapidez é `s = ‖v‖ = sqrt(vx² + vy² + vz²)`, invariante sob rotações de bases cartesianas ortonormais com as mesmas unidades. Não se tratam componentes de velocidade como graus/s nem se derivam latitude/longitude para inventar velocidades. As componentes angulares são carregadas, mas não são usadas para inferir uma convenção desconhecida.

### Aceleração

O gráfico distingue duas quantidades:

- **Linha contínua: `ds/dt = d‖v‖/dt` (m/s²)**, assinada; negativa significa redução da rapidez. É a componente tangencial quando a rapidez é não nula, não a magnitude da aceleração total. Uma curva a rapidez constante pode ter `ds/dt = 0` e aceleração não nula.
- **Linha pontilhada: `‖a_NED‖ = ‖dv_NED/dt‖` (m/s²)**, não negativa. Só é calculada quando a velocidade numa base NED fixa comum está confirmada. Nos logs reais, por defeito, fica **indisponível**, sem substituir por `‖dv_body/dt‖`.

A diferenciação usa `numpy.gradient` com três pontos e espaçamento temporal real não uniforme; nos extremos de segmentos com ≥3 pontos usa diferenças unilaterais de segunda ordem. Com dois pontos usa a secante; pontos isolados ficam indisponíveis. A época é subtraída em inteiros antes da conversão para segundos. NaN/Inf, `dt <= 0` e lacunas superiores a `max_gap_seconds` (2 s por defeito; os intervalos observados nos logs locais são cerca de 0,48–0,60 s) separam segmentos. Os gráficos não unem lacunas maiores que esse limite. Não há suavização: a derivada pode amplificar ruído; não se introduziu um filtro sem uma justificação física.

Após confirmação externa pelo produtor/docente, o YAML permite:

- `confirmed_velocity_frame: ned`: componentes já na base NED fixa comum.
- `confirmed_velocity_frame: body`: requer também `orientation.confirmed_body_to_ned_frame_id` e correspondência com `kinematics.body_frame_id`. Aplica-se `v_NED(t) = R(q(t)) v_body(t)` **antes** de derivar; a mudança da base ao longo do tempo fica incluída. Frames sem correspondência ficam indisponíveis.

A seleção de uma hipótese de orientação da vista local nunca autoriza aceleração vetorial. A demo fornece explicitamente velocidade NED e orientação conhecidas, permitindo exercitar também esta parte.

### Orientação e referenciais

Usamos quaterniões `(x,y,z,w)` normalizados. O README não especifica eixos do corpo, sentido da rotação ou ligação das orientações ao NED comum. `WGS84` identifica um sistema geodésico, não uma base de orientação do corpo.

Para preservar a funcionalidade anterior, `orientation.assumed_body_to_ned_frame_id: world_ned` mantém setas **provisórias**, identificadas nos títulos, e `p_local = R(q)^T (p_NED - p_centro)`. Configurar esse campo como `null` desliga a hipótese. Sem orientação utilizável do centro, a vista usa apenas translação NED. Setas dos outros robôs são transformadas para a mesma base local. As exportações distinguem `robot_body_assumed`, `robot_body_confirmed` e `ned_translated`.

O mapa só mostra rumo quando corpo → **NED fixo comum** está confirmado (demo por construção, ou `confirmed_body_to_ned_frame_id` preenchido após validação externa). O eixo X do corpo passa de NED comum para ECEF e para NED tangente na latitude/longitude atual; o rumo é `atan2(E, N)` desde Norte verdadeiro, no sentido horário. Um eixo vertical não define rumo. Isto não equivale a yaw ENU ou direção do movimento. Nos logs reais, com a configuração fornecida, não há setas geográficas.

### Painel «Mostrar a matemática»

O painel usa exatamente o mesmo snapshot do replay e inclui todas as amostras disponíveis, independentemente do filtro de proximidade. Mostra `T_NED←local = [R, t; 0, 1]`, a inversa analítica `[Rᵀ, −Rᵀt; 0, 1]` e `p_local = Rᵀ(p_NED − t)`. Sem orientação utilizável, `R = I` e a mudança é só uma translação. O estado distingue orientação confirmada, hipótese não validada e NED transladado.

As duas vistas **3D** mostram as posições e os segmentos entre pares com a mesma escala métrica nos eixos. Uma rotação rígida preserva as distâncias espaciais; a projeção no ecrã pode alterar a aparência do triângulo. A tabela compara `‖p_i − p_j‖` nas duas bases. As verificações usam precisão completa: `‖RᵀR − I‖_F < 10⁻¹²`, `|det(R) − 1| < 10⁻¹²`, reconstrução pela transformação inversa e distâncias com tolerância absoluta de 10⁻⁸ m e relativa de 10⁻¹². Matrizes e coordenadas apresentadas são arredondadas apenas para leitura.

Estes invariantes verificam a implementação de uma transformação rígida; **não comprovam a convenção física do quaternião**, o datum vertical ou a sincronização dos relógios. A tabela mostra o desvio temporal real de cada amostra face ao instante do slider, dentro da tolerância configurada; não sugere medições exatamente simultâneas. Se faltar a amostra do centro, o painel indica a indisponibilidade. O cálculo e a figura só são gerados enquanto o painel estiver aberto.

## Cartografia, atribuição e rede

Usamos [MapLibre](https://maplibre.org/maplibre-gl-js/docs/examples/add-a-raster-tile-source/) com mosaicos raster [OpenStreetMap](https://www.openstreetmap.org/copyright), a [camada seamark do OpenSeaMap](https://github.com/OpenSeaMap/online_chart/blob/master/dependencies.md) e polígonos de água OpenFreeMap/OpenMapTiles para o efeito 3D. As atribuições ficam visíveis no mapa. URLs e atribuições podem ser mudadas em `map` no YAML.

Respeitar a [política de mosaicos OSM](https://operations.osmfoundation.org/policies/tiles/): apenas a vista interativa, sem downloads em lote/offline, mantendo o Referer e a cache HTTP normal do browser. Os serviços são best-effort e a cobertura/disponibilidade de marcas náuticas pode variar. Uma falha de OpenSeaMap é indicada no estado do mapa. O mapa não é uma carta certificada de navegação.

Os provedores recebem pedidos dos mosaicos da área visualizada; as trajetórias GeoJSON permanecem entre o servidor local e o browser, sem upload para um serviço de mapas. Trajetórias completas e tempos relativos são enviados uma única vez num `dcc.Store`; os updates de replay contêm só poses atuais, índices das amostras e raio escolhido. Os rastos e o círculo são construídos no browser. A instância MapLibre/câmara é preservada. Os gráficos cinemáticos também são carregados uma vez, atualizando apenas o cursor via Dash `Patch`.

## Organização e testes

- `app.py`: layout Dash, callbacks, replay e exportações.
- `tomsa/data.py`: ZIP/demo, validação, dados geográficos, velocidades e metadados.
- `tomsa/coordinates.py`: geodésicas, rotações, AER e rumo geográfico.
- `tomsa/replay.py`: amostras sincronizadas, referencial local, snapshots e invariantes da transformação.
- `tomsa/figures.py`: vistas NED/local, comparação 3D dos referenciais e gráficos cinemáticos.
- `tomsa/kinematics.py` (novo): rapidez e diferenciação com lacunas.
- `tomsa/geography.py`, `assets/geography.js`, `assets/map_geometry.js` e `assets/ocean.js`: dados do mapa, integração MapLibre, rastos/círculo e material de água ilustrativo, sem frontend separado.
- `assets/style.css`, `config.yaml`, `tests/`: estilos, opções e validação.

```cmd
python -m pytest -q
```

O conjunto cobre a matemática anterior, invariantes rígidos 3D (incluindo um triângulo cuja projeção XY muda), inversas, estados de confirmação, offsets temporais, velocidade, diferenças não uniformes, lacunas, rotação de velocidades, conversão de rumo, sincronização de dados do mapa, callbacks Dash por HTTP, Play/Pause/fim e exportações. Se Node existir, pytest também executa os testes JS de ciclo do mapa/material oceânico; isoladamente: `node --test tests/test_geography.js tests/test_ocean.js`. Incluem rastos sem amostras futuras, lacunas e recuo temporal, raio/fecho do círculo, controlos sem reposicionar a câmara, recorte por classe ocean, ativação só em 3D, redução de movimento, paragem de timers e fallback do provedor. Não há pedidos a tiles nos testes automáticos. Testes de dados reais são assinalados como `skipped` quando o ZIP está ausente, sem bloquear os testes públicos sintéticos.

**Verificação gráfica por versão:** confirmar no browser local o aspeto responsivo, WebGL, carregamento CDN/tiles, zoom/rotação/inclinação, controlos dos efeitos e conservação da câmara durante Play/Pause/slider. Abrir/fechar o painel matemático e confirmar a atualização das tabelas e cenas ao mudar o instante/centro. Testes com objetos MapLibre simulados e HTTP não substituem uma verificação gráfica real.

A primeira entrega (`TOMSA_TL1_GRUPO07.ipynb`) está um nível acima deste projeto.
