%% DEMO 4 - Comparacao LBL vs SBL vs USBL em funcao da profundidade
% Trabalho PERSE - Posicionamento acustico subaquatico
% Monte Carlo do erro horizontal para um alvo perto do fundo.
%  LBL : 4 transponders no fundo (baseline 1000 m) + sensor de profundidade
%  SBL : 3 hidrofones no casco do navio (baseline L) + sensor de profundidade
%  USBL: transceiver unico, ruido angular 0.1 (topo de gama) ou 0.5 graus
close all; clc;
if exist('rng', 'file'), rng(3); else, randn('seed', 3); end

sigma_r = 0.10; sigma_z = 0.05; M = 300;
D = [100 250 500 1000 2000 3000];                 % profundidade da agua [m]
Lsbl = [20 50];                                    % baselines SBL [m]
rmsL = zeros(size(D)); rmsU = zeros(numel(D),2); sangs = [0.1 0.5]*pi/180; rmsS = zeros(numel(D), numel(Lsbl));

for i = 1:numel(D)
    p = [50 30 -(D(i)-20)];                        % alvo 20 m acima do fundo
    % ---- LBL ----
    B = [-500 -500 -D(i); 500 -500 -D(i); 500 500 -D(i); -500 500 -D(i)];
    e = zeros(M,1);
    for m = 1:M
        r  = sqrt(sum((B-p).^2,2)) + sigma_r*randn(4,1);
        pe = trilateracao(B, r, p + [5 5 0], p(3) + sigma_z*randn);
        e(m) = norm(pe(1:2)-p(1:2));
    end
    rmsL(i) = sqrt(mean(e.^2));
    % ---- SBL (hidrofones em triangulo no casco, z = 0) ----
    for j = 1:numel(Lsbl)
        L = Lsbl(j); H = [0 0 0; L 0 0; L/2 L*sqrt(3)/2 0];
        for m = 1:M
            r  = sqrt(sum((H-p).^2,2)) + sigma_r*randn(3,1);
            pe = trilateracao(H, r, p + [5 5 0], p(3) + sigma_z*randn);
            e(m) = norm(pe(1:2)-p(1:2));
        end
        rmsS(i,j) = sqrt(mean(e.^2));
    end
    % ---- USBL ----
    R = norm(p); u0 = p/R;
    for j = 1:2
        for m = 1:M
            un = u0 + sangs(j)*randn(1,3); un = un/norm(un);
            pe = (R + sigma_r*randn)*un;
            e(m) = norm(pe(1:2)-p(1:2));
        end
        rmsU(i,j) = sqrt(mean(e.^2));
    end
end

fprintf('%8s %9s %9s %9s %10s %10s\n', 'Prof.[m]', 'LBL', 'SBL 20m', 'SBL 50m', 'USBL 0.1', 'USBL 0.5');
for i = 1:numel(D)
    fprintf('%8d %9.3f %9.3f %9.3f %10.3f %10.3f\n', D(i), rmsL(i), rmsS(i,1), rmsS(i,2), rmsU(i,1), rmsU(i,2));
end

figure('Name', 'Demo4 - Comparacao');
loglog(D, rmsL, 'o-', 'LineWidth', 2); hold on; grid on;
loglog(D, rmsS(:,1), 's-', 'LineWidth', 2);
loglog(D, rmsS(:,2), 's--', 'LineWidth', 2);
loglog(D, rmsU(:,1), 'd-', 'LineWidth', 2);
loglog(D, rmsU(:,2), 'd--', 'LineWidth', 2);
legend('LBL (1000 m)', 'SBL (L = 20 m)', 'SBL (L = 50 m)', 'USBL (0.1\circ)', 'USBL (0.5\circ)', 'Location', 'northwest');
xlabel('Profundidade da agua [m]'); ylabel('Erro horizontal RMS [m]');
title('Erro horizontal vs profundidade (mesmo ruido de distancia: 0.1 m)');
