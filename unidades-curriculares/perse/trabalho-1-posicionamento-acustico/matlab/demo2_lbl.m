%% DEMO 2 - LBL (Long Baseline): trilateracao com transponders no fundo
% Trabalho PERSE - Posicionamento acustico subaquatico
% O ROV interroga 4 transponders fixos no fundo; cada um responde.
% Tempo de ida e volta (TWTT) -> distancia -> posicao por minimos quadrados.
close all; clc;
if exist('rng', 'file'), rng(1); else, randn('seed', 1); end

c       = 1500;     % velocidade do som assumida [m/s]
sigma_t = 0.13e-3;  % ruido no TWTT [s] -> ~0.1 m em distancia
sigma_z = 0.05;     % ruido do sensor de profundidade [m]
z_fundo = -500;     % fundo a 500 m

% --- Transponders (baseline ~1000 m) ------------------------------------
B = [   0    0  z_fundo+5;
     1000    0  z_fundo+5;
     1000 1000  z_fundo+5;
        0 1000  z_fundo+5];

% --- Trajetoria do ROV ("lawnmower") a 450 m de profundidade -----------
x = 100:10:900; P = [];
for k = 1:4
    yk = 200*k; xs = x; if mod(k,2)==0, xs = fliplr(x); end
    P = [P; xs' yk*ones(numel(xs),1) -450*ones(numel(xs),1)];
end
N = size(P,1);

est3D = zeros(N,3); est2D = zeros(N,3);
p3 = [500 500 -400]; p2 = p3;          % estimativas iniciais
for n = 1:N
    rho  = sqrt(sum((B - P(n,:)).^2, 2));       % distancias reais
    twtt = 2*rho/c + sigma_t*randn(4,1);        % tempo ida e volta medido
    r    = c*twtt/2;                            % distancia medida
    zmed = P(n,3) + sigma_z*randn;              % sensor de pressao
    p3 = trilateracao(B, r, p3);                % 3D, so acustica
    p2 = trilateracao(B, r, p2, zmed);          % 2D + profundidade
    est3D(n,:) = p3; est2D(n,:) = p2;
end
eh3 = sqrt(sum((est3D(:,1:2)-P(:,1:2)).^2, 2));
eh2 = sqrt(sum((est2D(:,1:2)-P(:,1:2)).^2, 2));
fprintf('Erro horizontal RMS (so acustica, 3D)   = %.3f m\n', sqrt(mean(eh3.^2)));
fprintf('Erro horizontal RMS (acustica + depth)  = %.3f m\n', sqrt(mean(eh2.^2)));
fprintf('Erro vertical RMS   (so acustica, 3D)   = %.3f m\n', sqrt(mean((est3D(:,3)-P(:,3)).^2)));
fprintf('Erro vertical RMS   (acustica + depth)  = %.3f m  (= sensor de pressao)\n', sigma_z);
% Nota: com os transponders todos ao mesmo nivel, a geometria vertical e
% fraca -> o sensor de profundidade resolve a componente z.

% --- Mapa de HDOP (qualidade da geometria) -------------------------------
[gx, gy] = meshgrid(-600:25:1600, -600:25:1600);
hdop = zeros(size(gx));
for i = 1:numel(gx)
    d = B - [gx(i) gy(i) -450];
    J = -d(:,1:2) ./ sqrt(sum(d.^2, 2));
    hdop(i) = sqrt(trace(inv(J'*J)));
end

figure('Name', 'Demo2 - LBL');
subplot(1,2,1); hold on; grid on; axis equal;
contourf(gx, gy, min(hdop, 5), 20, 'LineColor', 'none'); colorbar;
plot(P(:,1), P(:,2), 'k-', 'LineWidth', 1.5);
plot(est2D(:,1), est2D(:,2), 'r.', 'MarkerSize', 6);
plot(B(:,1), B(:,2), 'w^', 'MarkerFaceColor', 'y', 'MarkerSize', 10);
xlabel('x [m]'); ylabel('y [m]');
title('LBL: trajetoria e mapa de HDOP (cor)');

subplot(1,2,2); hold on; grid on;
plot(eh3, 'DisplayName', 'So acustica (3D)');
plot(eh2, 'DisplayName', 'Acustica + profundidade');
xlabel('Ping'); ylabel('Erro horizontal [m]'); legend;
title('Erro de posicao por ping');
