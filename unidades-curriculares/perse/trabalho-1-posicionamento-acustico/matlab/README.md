# Código MATLAB — posicionamento acústico subaquático (LBL / SBL / USBL)
Exemplos didáticos em MATLAB (testados também em GNU Octave). Não usam toolboxes.

## Demo interativa (principal)
`demo_interativa` — abre uma janela com: vista de cima (clicar move o alvo), erro no alvo (elipses 95 % + vieses), perfil de velocidade do som real vs usado, decomposição aleatório/sistemático e painel com valores medidos publicados. Sliders: profundidade, frequência, estado do mar, nível de fonte, rede LBL, baseline SBL, abertura USBL, erro de heading; menu: velocidade do som usada pelo sistema.

Dados reais (pasta `dados/`): perfis Argo (T, S, pressão) a oeste de Lisboa, julho–agosto de 2025, obtidos do ERDDAP do Ifremer (Argo, doi:10.17882/42182). O perfil “verdadeiro” é o da bóia 6901998 a 20/07/2025 (38,67°N 12,55°W, modo delayed, 593 níveis até 1998 dbar).

| Parâmetro | Valor / intervalo | Fonte |
|---|---|---|
| Perfil de c(z) | perfis Argo reais + Mackenzie (1981) | Argo / Ifremer ERDDAP; Mackenzie JASA 1981 |
| Absorção | Thorp | Kibblewhite & Hampton 1980 (validade 0,1–100 kHz) |
| Ruído ambiente | 94,5 − (50/3)·log10(f) + 30·log10(SS+1) dB re 1 µPa²/Hz | Kurahashi & Gratta, arXiv:0712.1833 (ajuste a Urick/Knudsen, 1–40 kHz) |
| Nível de fonte | 181–199 dB re 1 µPa @ 1 m (omissão 187) | Sonardyne WMT/transponders MF |
| Heading do navio | 0,1° (AHRS) a 1° (instalação não calibrada) | Sonardyne; Liu et al. 2023 |
| Banda / duração do sinal | B = min(10 kHz, 0,4 f), T = 5 ms | parâmetro de projeto (banda MF 20–34 kHz, Sonardyne) |
| Erro aleatório | limite de Cramér–Rao do tempo de chegada | ver documento técnico, secção 4.3 |

Resultados de referência (alvo (300, 200) m, fundo a 1000 m, 25 kHz, SS3): erro total LBL / SBL / USBL = 1,19 / 17,4 / 2,33 m com c = 1500 m/s; 0,04 / 0,74 / 1,05 m com o perfil Argo de 10 dias depois; 0,00 / 0,63 / 1,05 m com o perfil exato.


| Ficheiro | Conteúdo |
|---|---|
| `correr_tudo.m` | Corre as 4 demos e guarda as figuras em `figuras/` |
| `demo1_velocidade_som.m` | Perfil de velocidade do som (Mackenzie 1981) e erro de distância Δr = r·Δc/c |
| `demo2_lbl.m` | LBL: trilateração Gauss-Newton com 4 transponders, efeito do sensor de profundidade, mapa de HDOP |
| `demo3_usbl.m` | USBL: chirp 20–30 kHz + filtro adaptado + diferença de fase (λ/2), par longo (2λ) com resolução de ambiguidade; erro vs SNR; erro vs distância e desalinhamento de heading |
| `demo4_comparacao.m` | Monte Carlo LBL vs SBL vs USBL em função da profundidade (LBL e SBL com sensor de profundidade) |
| `demo5_orcamento_enlace.m` | Absorção de Thorp e equação do sonar: SNR vs distância a 15/25/50 kHz |
| `demo6_kalman_lbl_dvl.m` | EKF LBL + DVL com rejeição de outliers (Mahalanobis) vs dead reckoning vs LBL ponto a ponto |
| `thorp.m` | Coeficiente de absorção de Thorp [dB/km] |
| `modelo_posicionamento.m` | Núcleo da demo interativa: erro aleatório (CRLB) e sistemático (c, heading) de LBL/SBL/USBL |
| `carregar_argo.m`, `c_media.m`, `ruido_ambiente.m` | Leitura dos perfis Argo, velocidade média harmónica, ruído ambiente |
| `mackenzie.m` | Equação de 9 termos de Mackenzie para c(T,S,D) |
| `trilateracao.m` | Mínimos quadrados não lineares (Gauss-Newton), opção de profundidade conhecida |
| `usbl_ping.m` | Simulação de um ping USBL ao nível do sinal (opção de par longo + resolução de ambiguidade) |

Resultados de referência (seeds fixas, Octave 8):
- demo2: erro horizontal RMS ≈ 0,10 m; vertical 0,66 m (só acústica) → 0,05 m (com sensor de pressão)
- demo3: a 1000 m, erro RMS ≈ 2,4 m (σθ = 0,1°) e ≈ 9 m com 1° de heading
- demo3: com par longo o erro cai ~4x (0 dB: 1,6 % → 0,5 % do slant range)
- demo4: LBL ≈ 0,1 m constante; a 1000 m: SBL 20 m ≈ 7,4 m, SBL 50 m ≈ 3,5 m, USBL 0,1° ≈ 2,4 m
- demo5: alcance com SNR ≥ 10 dB: 12 km (15 kHz), 6,3 km (25 kHz), 2,9 km (50 kHz) — compatível com as especificações MF (7 km) e LMF (> 11 km) da Sonardyne
- demo6: erro RMS 17 m só DVL, 10 m LBL ponto a ponto, 0,29 m EKF

## Referências
Ver o [documento técnico](../docs/base-tecnica.md) para a lista completa (inclui Kinsey et al. 2006, Paull et al. 2014, Eustice et al. 2011, Alcocer/Oliveira/Pascoal 2006).

1. Wikipedia, Underwater acoustic positioning system — https://en.wikipedia.org/wiki/Underwater_acoustic_positioning_system
2. Wikipedia, LBL / SBL / USBL — https://en.wikipedia.org/wiki/Long_baseline_acoustic_positioning_system , https://en.wikipedia.org/wiki/Short_baseline_acoustic_positioning_system , https://en.wikipedia.org/wiki/Ultra-short_baseline_acoustic_positioning_system
3. Revisão de sistemas USBL comerciais — https://bibliotekanauki.pl/articles/985799.pdf
4. K. V. Mackenzie, "Nine-term equation for sound speed in the oceans", J. Acoust. Soc. Am. 70(3), 807–812, 1981. doi:10.1121/1.386920
5. Liu et al., calibração do ângulo de instalação USBL, Polish Maritime Research 2/2023 — https://reference-global.com/download/article/10.2478/pomr-2023-0028.pdf
6. Sonardyne, Ranger 2 / HPT — https://www.sonardyne.com/technology/sensor-tracking/
7. Kongsberg, HiPAP 602 datasheet — https://www.kongsberg.com/globalassets/discovery/commerce/navigation--positioning/hipap-602/476666a-hipap-602-datasheet.pdf
8. Unique Group, USBL vs LBL — https://www.uniquegroup.com/media-centre/blog-articles/usbl-vs-lbl-systems/
9. Hydro International, LBL Underwater Positioning (2008) — https://www.hydro-international.com/content/article/lbl-underwater-positioning
10. Hydro International, Wideband Signals the Future for Acoustic Positioning — https://www.hydro-international.com/content/article/wideband-signals-the-future-for-acoustic-positioning
11. Fernandes, Sahoo, Kothari, Cooperative Localization for AUVs — a comprehensive review, arXiv:2307.06189 — https://arxiv.org/abs/2307.06189
