function demo_interativa()
%DEMO_INTERATIVA Posicionamento acustico subaquatico: LBL vs SBL vs USBL.
%   Trabalho PERSE (MEEC, ISEP). Demo interativa com dados reais.
%
%   Como usar:
%     - clique na vista de cima (esquerda) para mudar a posicao do alvo;
%     - mexa nos sliders (profundidade, frequencia, estado do mar, ...);
%     - escolha a velocidade do som que o sistema USA (menu): o perfil
%       VERDADEIRO e sempre o perfil Argo real de 20/07/2025.
%
%   Dados reais e fontes (ver README e documento tecnico):
%     perfil T/S: boia Argo 6901998, 20/07/2025, 38.67N 12.55W (oeste de Lisboa)
%     absorcao: Thorp; ruido ambiente: ajuste de Urick/Knudsen (Kurahashi & Gratta, arXiv:0712.1833)
%     nivel de fonte: transponders Sonardyne MF (187-199 dB re 1 uPa @ 1 m)
%     heading do navio: 0,1 graus (AHRS Sonardyne) ate 1 grau (instalacao nao calibrada)
%
%   Funciona em MATLAB e em GNU Octave (toolkit qt). Ficheiros necessarios
%   na mesma pasta: modelo_posicionamento.m, carregar_argo.m, c_media.m,
%   ruido_ambiente.m, thorp.m, mackenzie.m e a pasta dados/.

aqui = fileparts(mfilename('fullpath'));
[g.zv, g.cv] = carregar_argo(fullfile(aqui, 'dados', 'argo_6901998_2025-07-20.csv'));
[g.zA, g.cA] = carregar_argo(fullfile(aqui, 'dados', 'argo_6901998_2025-07-30.csv'));
[g.zB, g.cB] = carregar_argo(fullfile(aqui, 'dados', 'argo_7901143_2025-07-14.csv'));
g.perfis = {'1500 m/s constante (sem medir)', ...
            'Argo 6901998, 10 dias depois (~70 km)', ...
            'Argo 7901143, 6 dias antes (~170 km)', ...
            'Perfil exato (o verdadeiro)'};
g.alvo = [300 200];

f = figure('Name', 'PERSE - Posicionamento acustico: LBL vs SBL vs USBL', ...
           'NumberTitle', 'off', 'Units', 'pixels', 'Position', [40 40 1400 820], 'Color', 'w');

% ---------------- eixos ----------------
g.axP = axes('Parent', f, 'Position', [0.045 0.42 0.27 0.52]);   % planta
g.axZ = axes('Parent', f, 'Position', [0.37 0.42 0.27 0.52]);    % zoom no alvo
g.axC = axes('Parent', f, 'Position', [0.695 0.56 0.10 0.38]);    % perfil c(z)
g.axB = axes('Parent', f, 'Position', [0.37 0.07 0.27 0.25]);    % barras de erro
g.txt = uicontrol(f, 'Style', 'text', 'Units', 'normalized', 'Position', [0.815 0.42 0.183 0.53], ...
                  'HorizontalAlignment', 'left', 'BackgroundColor', 'w', 'FontSize', 9);
g.ref = uicontrol(f, 'Style', 'text', 'Units', 'normalized', 'Position', [0.68 0.03 0.31 0.33], ...
                  'HorizontalAlignment', 'left', 'BackgroundColor', [0.96 0.97 0.97], 'FontSize', 9, ...
                  'String', texto_referencias());

% ---------------- controlos ----------------
%            nome                         min    max    valor  formato
ctl = { 'D',      'Profundidade da agua [m]',    100,   1950,  1000, '%.0f';
        'f',      'Frequencia central [kHz]',     10,     50,    25, '%.1f';
        'SS',     'Estado do mar (0-6)',           0,      6,     3, '%.0f';
        'SL',     'Nivel de fonte [dB]',         181,    199,   187, '%.0f';
        'Llbl',   'Lado da rede LBL [m]',        300,   3000,  1000, '%.0f';
        'Lsbl',   'Baseline SBL [m]',             10,     60,    30, '%.0f';
        'd_usbl', 'Abertura USBL [cm]',            3,     20,     3, '%.0f';
        'hdg',    'Erro de heading [graus]',       0,      1,   0.1, '%.2f' };
g.ctl = ctl;
n = size(ctl, 1);
for k = 1:n
    y = 0.33 - (k-1)*0.036;
    uicontrol(f, 'Style', 'text', 'Units', 'normalized', 'Position', [0.01 y 0.15 0.03], ...
              'String', ctl{k,2}, 'HorizontalAlignment', 'left', 'BackgroundColor', 'w');
    g.sl.(ctl{k,1}) = uicontrol(f, 'Style', 'slider', 'Units', 'normalized', 'Position', [0.16 y+0.005 0.13 0.025], ...
              'Min', ctl{k,3}, 'Max', ctl{k,4}, 'Value', ctl{k,5}, 'Callback', @(s, e) atualizar(f));
    g.val.(ctl{k,1}) = uicontrol(f, 'Style', 'text', 'Units', 'normalized', 'Position', [0.295 y 0.04 0.03], ...
              'String', sprintf(ctl{k,6}, ctl{k,5}), 'BackgroundColor', 'w');
end
uicontrol(f, 'Style', 'text', 'Units', 'normalized', 'Position', [0.01 0.03 0.15 0.03], ...
          'String', 'Velocidade do som usada', 'HorizontalAlignment', 'left', 'BackgroundColor', 'w');
g.menu = uicontrol(f, 'Style', 'popupmenu', 'Units', 'normalized', 'Position', [0.16 0.035 0.18 0.03], ...
                   'String', g.perfis, 'Value', 1, 'Callback', @(s, e) atualizar(f));

set(g.axP, 'ButtonDownFcn', @(s, e) clique(f));
guidata(f, g);
atualizar(f);
end

% =====================================================================
function clique(f)
g = guidata(f);
cp = get(g.axP, 'CurrentPoint');
g.alvo = cp(1, 1:2);
guidata(f, g);
atualizar(f);
end

% =====================================================================
function atualizar(f)
g = guidata(f);
for k = 1:size(g.ctl, 1)
    v = get(g.sl.(g.ctl{k,1}), 'Value');
    if any(strcmp(g.ctl{k,1}, {'D', 'SS', 'SL', 'Llbl', 'Lsbl', 'd_usbl'})), v = round(v); end
    P.(g.ctl{k,1}) = v;
    set(g.val.(g.ctl{k,1}), 'String', sprintf(g.ctl{k,6}, v));
end
P.d_usbl = P.d_usbl / 100;                 % cm -> m
P.B = min(10e3, 0.4*P.f*1e3);  P.T = 5e-3;  % sinal: banda <= 40 % de f, 5 ms
P.alvo = g.alvo;  P.zv = g.zv;  P.cv = g.cv;
switch get(g.menu, 'Value')
    case 1, P.zc = [0 6000]; P.cc = [1500 1500];
    case 2, P.zc = g.zA; P.cc = g.cA;
    case 3, P.zc = g.zB; P.cc = g.cB;
    otherwise, P.zc = g.zv; P.cc = g.cv;
end
R = modelo_posicionamento(P);
delete(findobj(f, 'Tag', 'legend'));        % legendas antigas (MATLAB e Octave)
sis = {'LBL', 'SBL', 'USBL'};
cor = [0.12 0.61 0.56; 0.85 0.47 0.17; 0.15 0.39 0.66];

% ---------- planta ----------
ax = g.axP;  cla(ax);  hold(ax, 'on');
h = P.Llbl/2;
lim = max([h*1.4, abs(g.alvo)*1.2, 400]);
plot(ax, [-h h h -h], [-h -h h h], '^', 'MarkerSize', 9, 'MarkerFaceColor', cor(1,:), 'Color', cor(1,:), 'HitTest', 'off');
L = P.Lsbl;
plot(ax, [-L/2 L/2 0], [-L/(2*sqrt(3)) -L/(2*sqrt(3)) L/sqrt(3)], 'o', 'MarkerFaceColor', cor(2,:), 'Color', cor(2,:), 'HitTest', 'off');
plot(ax, 0, 0, 's', 'MarkerSize', 10, 'MarkerFaceColor', cor(3,:), 'Color', cor(3,:), 'HitTest', 'off');
plot(ax, g.alvo(1), g.alvo(2), 'kx', 'MarkerSize', 14, 'LineWidth', 2.5, 'HitTest', 'off');
axis(ax, 'equal');  xlim(ax, [-lim lim]);  ylim(ax, [-lim lim]);  grid(ax, 'on');
xlabel(ax, 'x [m]');  ylabel(ax, 'y [m]');
title(ax, {'Vista de cima (clique para mover o alvo)', '\^ transponders LBL   o hidrofones SBL   [] navio/USBL'});

% ---------- zoom no alvo: elipses 95 % + vies ----------
ax = g.axZ;  cla(ax);  hold(ax, 'on');
ext = 0.05;  hl = zeros(1,4);
for k = 1:3
    X = R.(sis{k});
    [ex, ey] = elipse(X.C, 2.45);
    hl(k) = plot(ax, X.b(1) + ex, X.b(2) + ey, '-', 'Color', cor(k,:), 'LineWidth', 2);
    plot(ax, [0 X.b(1)], [0 X.b(2)], '--', 'Color', cor(k,:), 'LineWidth', 1.2);
    plot(ax, X.b(1), X.b(2), 'o', 'Color', cor(k,:), 'MarkerFaceColor', cor(k,:));
    ext = max([ext, abs(X.b') + 2.45*sqrt(max(eig(X.C)))]);
end
hl(4) = plot(ax, 0, 0, 'kx', 'MarkerSize', 14, 'LineWidth', 2.5);
axis(ax, 'equal');  xlim(ax, 1.15*[-ext ext]);  ylim(ax, 1.15*[-ext ext]);  grid(ax, 'on');
xlabel(ax, 'erro em x [m]');  ylabel(ax, 'erro em y [m]');
legend(ax, hl, {'LBL', 'SBL', 'USBL', 'alvo real'}, 'Location', 'northwest');
title(ax, {'Erro no alvo: elipse 95 % (aleatorio)', 'tracejado = vies (velocidade do som, heading)'});

% ---------- perfil c(z) ----------
ax = g.axC;  cla(ax);  hold(ax, 'on');
plot(ax, g.cv, g.zv, 'k-', 'LineWidth', 1.8);
plot(ax, P.cc, P.zc, 'r--', 'LineWidth', 1.5);
plot(ax, [1490 1535], P.D*[1 1], ':', 'Color', [0.4 0.3 0.2]);
set(ax, 'YDir', 'reverse');  ylim(ax, [0 2000]);  xlim(ax, [1490 1535]);  grid(ax, 'on');
xlabel(ax, 'c [m/s]');  ylabel(ax, 'profundidade [m]');
title(ax, {'Perfil real (preto)', 'vs usado (vermelho)'});

% ---------- barras: aleatorio vs vies ----------
ax = g.axB;  cla(ax);
ea = zeros(3,1);  eb = zeros(3,1);
for k = 1:3
    ea(k) = sqrt(trace(R.(sis{k}).C));
    eb(k) = norm(R.(sis{k}).b);
end
hb = bar(ax, [max(ea, 1e-4) max(eb, 1e-4)]);
set(hb, 'BaseValue', 1e-4);
set(ax, 'YScale', 'log', 'XTickLabel', sis);  grid(ax, 'on');
ylim(ax, [1e-4 max([ea; eb; 1])*3]);
ylabel(ax, 'erro horizontal [m]');
legend(ax, hb, {'aleatorio (RMS)', 'sistematico (vies)'}, 'Location', 'northwest');
title(ax, 'O que domina o erro?');

% ---------- texto de resultados ----------
cmu = c_media(P.zc, P.cc, 0, P.D-20);  cmv = c_media(g.zv, g.cv, 0, P.D-20);
s = {sprintf('Alvo: (%.0f, %.0f) m a %.0f m', g.alvo, P.D-20), ...
     sprintf('Slant range USBL: %.0f m', R.r_usbl), '', ...
     sprintf('Ruido ambiente (SS %d): %.1f dB', P.SS, R.NL), ...
     sprintf('Ganho filtro adaptado: %.1f dB', R.G), ...
     sprintf('SNR (apos filtro):'), ...
     sprintf('  LBL %.0f | SBL %.0f | USBL %.0f dB', R.snr_lbl, R.snr_sbl, R.snr_usbl), '', ...
     sprintf('c media real (0-%.0f m):', P.D-20), sprintf('  %.1f m/s', cmv), ...
     sprintf('c media usada: %.1f m/s', cmu), ...
     sprintf('  -> erro de escala %.2f %%', 100*(cmu/cmv - 1)), '', 'Erro horizontal total:'};
for k = 1:3
    tot = sqrt(ea(k)^2 + eb(k)^2);
    s{end+1} = sprintf('%-4s %7.3f m (%.3f %% R)', sis{k}, tot, 100*tot/R.r_usbl); %#ok<AGROW>
end
lam = 1500/(P.f*1e3);
if P.d_usbl > lam/2
    s{end+1} = '';
    s{end+1} = sprintf('USBL: d = %.0f cm > lambda/2 = %.1f cm', 100*P.d_usbl, 100*lam/2);
    s{end+1} = '  -> fase ambigua: exige par curto';
    s{end+1} = '     extra (ver demo3_usbl.m)';
end
if any([R.snr_lbl R.snr_sbl R.snr_usbl] < 10)
    s{end+1} = '';
    s{end+1} = 'ATENCAO: SNR < 10 dB -> sem detecao fiavel!';
end
s{end+1} = '';
s{end+1} = 'Aleatorio = limite teorico (CRLB).';
s{end+1} = 'Real: + multipercurso, refracao,';
s{end+1} = '        calibracao (ver painel).';
set(g.txt, 'String', s);
end

% =====================================================================
function [ex, ey] = elipse(C, k)
t = linspace(0, 2*pi, 80);
[V, Dg] = eig((C + C')/2);
xy = V * sqrt(max(Dg, 0)) * [cos(t); sin(t)] * k;
ex = xy(1,:);  ey = xy(2,:);
end

% =====================================================================
function s = texto_referencias()
s = {'Valores MEDIDOS publicados (para comparar com a demo):', ...
     ' LBL 12 kHz: 0,1-10 m, ate 10 km (Kinsey et al. 2006)', ...
     ' LBL 300 kHz: +-7 mm a ~100 m (Kinsey et al. 2006)', ...
     ' SBL Jason/Medea (WHOI): 0,09 m', ...
     ' SBL SCINI, baseline ~35 m: 0,54 m', ...
     ' USBL tipico: 0,5-2 % do slant range (Unique Group)', ...
     ' USBL topo: 0,04 % (Sonardyne Ranger 2), 0,04 graus (HiPAP 602)', ...
     ' Raspi2USBL (lago/mar): dist. < 0,1 %, dir. <= 0,1 graus', '', ...
     'A demo da o limite teorico + erros sistematicos;', ...
     'a diferenca para os valores medidos e o que', ...
     'multipercurso, refracao e calibracao custam.'};
end
