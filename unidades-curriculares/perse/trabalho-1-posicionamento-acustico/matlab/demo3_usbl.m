%% DEMO 3 - USBL (Ultra-Short Baseline): distancia + angulo por diferenca de fase
% Trabalho PERSE - Posicionamento acustico subaquatico
% Parte A: um "ping" simulado ao nivel do sinal
%   chirp 20-30 kHz -> filtro adaptado (matched filter) -> tempo de chegada
%   diferenca de fase entre hidrofones a lambda/2 -> cossenos diretores
%   par longo (2*lambda) + resolucao de ambiguidade -> 4x mais preciso
% Parte B: erro de posicao vs distancia (Monte Carlo) e efeito de um
%   desalinhamento de heading na instalacao do transceiver
close all; clc;
if exist('rng', 'file'), rng(2); else, randn('seed', 2); end

%% ---------------- PARTE A: processamento de sinal -----------------------
p     = [300 -150 -600];   % transponder (alvo) [m]
SNRdB = 0;                 % SNR por amostra ANTES do filtro adaptado
[pest, Rm, x, y, n0, fs] = usbl_ping(p, SNRdB);
env = abs(y(:,1)); Nw = size(x,1);

fprintf('Distancia real = %.2f m | medida = %.2f m\n', norm(p), Rm);
fprintf('Posicao real : [%7.2f %7.2f %7.2f]\n', p);
fprintf('Posicao USBL : [%7.2f %7.2f %7.2f]\n', pest);
fprintf('Erro 3D = %.2f m (%.2f %% do slant range)\n', norm(pest-p), 100*norm(pest-p)/norm(p));

% Efeito do SNR e da resolucao de ambiguidade (par curto lambda/2 vs
% par curto + par longo 2*lambda = 12 cm). 20 pings por SNR (demora ~1 min).
SNRs = [-10 -5 0 5 10]; M = 20; mLong = 2;
fprintf('\nSNR [dB] | erro so par curto [%% R] | erro com par longo [%% R] | saltos de ambiguidade\n');
for q = 1:numel(SNRs)
    e1 = zeros(M,1); e2 = zeros(M,1);
    for m = 1:M
        [pl, ~, ~, ~, ~, ~, pc] = usbl_ping(p, SNRs(q), mLong);
        e1(m) = norm(pc - p); e2(m) = norm(pl - p);
    end
    saltos = sum(e2 > 0.1*norm(p));          % k errado => erro de ~50 % de R
    fprintf('%8d | %24.2f | %24.2f | %d de %d\n', SNRs(q), 100*mean(e1)/norm(p), 100*median(e2)/norm(p), saltos, M);
end

tt = (0:Nw-1)/fs;
win = n0 + (-2000:2000);
figure('Name', 'Demo3A - USBL sinal');
subplot(2,1,1);
plot(tt(win)*1e3, x(win,1)); grid on;
xlabel('t [ms]'); ylabel('x_1(t)');
title(sprintf('Sinal recebido no hidrofone 1 (SNR = %d dB por amostra)', SNRdB));
subplot(2,1,2);
plot(tt(win)*1e3, env(win)/max(env), 'LineWidth', 1.5); grid on; hold on;
plot(tt(n0)*1e3, 1, 'ro', 'MarkerSize', 8);
xlabel('t [ms]'); ylabel('|y_1(t)| (norm.)');
title('Saida do filtro adaptado: pico = tempo de chegada (ganho de processamento BT = 50)');

%% ---------------- PARTE B: erro vs distancia ----------------------------
sigma_ang = 0.1*pi/180;    % ruido angular [rad] (0.1 graus)
sigma_r   = 0.10;          % ruido de distancia [m]
Rlist     = 100:100:3000;  % slant range [m]
erro_hd   = [0 0.5 1];     % desalinhamento de heading [graus]
M = 500;  rms_h = zeros(numel(Rlist), numel(erro_hd));
for j = 1:numel(erro_hd)
    a = erro_hd(j)*pi/180; Rz = [cos(a) -sin(a) 0; sin(a) cos(a) 0; 0 0 1];
    for i = 1:numel(Rlist)
        R  = Rlist(i);
        u0 = [sind(30)*cosd(20) sind(30)*sind(20) -cosd(30)];  % alvo a 30 graus da vertical
        e2 = zeros(M,1);
        for m = 1:M
            un = u0 + sigma_ang*randn(1,3); un = un/norm(un);  % ruido angular
            pe = (R + sigma_r*randn) * (Rz*un')';               % + desalinhamento
            e2(m) = sum((pe(1:2) - R*u0(1:2)).^2);
        end
        rms_h(i,j) = sqrt(mean(e2));
    end
end
figure('Name', 'Demo3B - USBL erro vs distancia');
subplot(1,2,1); hold on; grid on;
for j = 1:numel(erro_hd)
    plot(Rlist, rms_h(:,j), 'LineWidth', 2, 'DisplayName', sprintf('heading off. = %.1f\\circ', erro_hd(j)));
end
xlabel('Slant range [m]'); ylabel('Erro horizontal RMS [m]'); legend('Location', 'northwest');
title('USBL: o erro cresce com a distancia');
subplot(1,2,2); hold on; grid on;
for j = 1:numel(erro_hd)
    plot(Rlist, 100*rms_h(:,j)./Rlist', 'LineWidth', 2);
end
xlabel('Slant range [m]'); ylabel('Erro / slant range [%]');
title('Erro em % do slant range (~constante)');
fprintf('A 1000 m: erro RMS = %.2f m (0 graus), %.2f m (1 grau de heading)\n', ...
        rms_h(Rlist==1000,1), rms_h(Rlist==1000,3));
