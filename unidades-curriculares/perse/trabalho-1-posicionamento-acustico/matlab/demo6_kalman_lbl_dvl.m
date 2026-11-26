%% DEMO 6 - Fusao LBL + DVL com filtro de Kalman estendido
% Trabalho PERSE - Posicionamento acustico subaquatico
% Compara: (a) dead reckoning so com DVL (deriva)
%          (b) LBL ponto a ponto a cada ciclo (ruido + outliers de multipercurso)
%          (c) EKF: predicao com DVL, atualizacao com cada distancia LBL,
%              rejeicao de outliers por teste de Mahalanobis (chi2 = 6.63)
close all; clc;
if exist('rng', 'file'), rng(6); else, randn('seed', 6); rand('seed', 6); end

dt = 1;  Tlbl = 5;           % DVL a 1 Hz, ciclo LBL a cada 5 s (12 kHz, lento)
sig_v = 0.02;                % ruido do DVL [m/s]
corr  = [0.005 -0.004];      % vies do DVL (desalinhamento/escala, ~0,6 % de 1 m/s) [m/s]
sig_r = 0.5;  p_out = 0.10;  % ruido LBL [m] e prob. de outlier (multipercurso)
z = -450;  B = [0 0 -495; 1000 0 -495; 1000 1000 -495; 0 1000 -495];

% Trajetoria real: vaivem a 1 m/s
P = []; V = [];
for k = 1:4
    yk = 200*k; xs = 100:1:900; if mod(k,2)==0, xs = fliplr(xs); end
    P = [P; xs' yk*ones(numel(xs),1)];
    V = [V; sign(xs(end)-xs(1))*ones(numel(xs),1) zeros(numel(xs),1)];
    if k < 4, ys = (yk+1:yk+199)'; P = [P; xs(end)*ones(numel(ys),1) ys]; V = [V; zeros(numel(ys),1) ones(numel(ys),1)]; end
end
N = size(P,1);

% (a) dead reckoning
dr = zeros(N,2); dr(1,:) = P(1,:);
% (c) EKF: estado [x y bx by]
x = [P(1,:) 0 0]'; Pc = diag([1 1 0.1^2 0.1^2]);
Q = diag([(sig_v*dt)^2 (sig_v*dt)^2 (1e-4)^2 (1e-4)^2]);
ekf = zeros(N,2); ekf(1,:) = P(1,:); lbl = nan(N,2); nrej = 0; nout = 0; pfix = [500 500];
for n = 2:N
    vmed = V(n-1,:) + corr + sig_v*randn(1,2);           % medida DVL (com vies)
    dr(n,:) = dr(n-1,:) + vmed*dt;
    F = [eye(2) dt*eye(2); zeros(2) eye(2)];
    x = F*x + [vmed'*dt; 0; 0];  Pc = F*Pc*F' + Q;       % predicao
    if mod(n, Tlbl) == 0
        rho = sqrt(sum((B - [P(n,:) z]).^2, 2));
        r = rho + sig_r*randn(4,1);
        out = rand(4,1) < p_out; r(out) = r(out) + 5 + 45*rand(sum(out),1); nout = nout + sum(out);
        pfix = trilateracao(B, r, [pfix(1:2) z], z); lbl(n,:) = pfix(1:2);  % (b)
        for i = 1:4                                       % (c) atualizacoes
            d = [x(1:2)' z] - B(i,:); h = norm(d);
            H = [d(1:2)/h 0 0];
            S = H*Pc*H' + sig_r^2; nu = r(i) - h;
            if nu^2/S > 6.63, nrej = nrej + 1; continue; end
            K = Pc*H'/S;  x = x + K*nu;  Pc = (eye(4) - K*H)*Pc;
        end
    end
    ekf(n,:) = x(1:2)';
end
e_dr  = sqrt(sum((dr - P).^2, 2));
e_ekf = sqrt(sum((ekf - P).^2, 2));
ok = ~isnan(lbl(:,1)); e_lbl = sqrt(sum((lbl(ok,:) - P(ok,:)).^2, 2));
fprintf('Erro horizontal RMS:\n');
fprintf('  (a) so DVL (dead reckoning): %6.2f m  (final %.1f m)\n', sqrt(mean(e_dr.^2)), e_dr(end));
fprintf('  (b) LBL ponto a ponto:       %6.2f m  (max %.1f m, por causa dos outliers)\n', sqrt(mean(e_lbl.^2)), max(e_lbl));
fprintf('  (c) EKF LBL + DVL:           %6.2f m\n', sqrt(mean(e_ekf.^2)));
fprintf('Outliers gerados: %d | medidas rejeitadas pelo teste: %d\n', nout, nrej);
fprintf('Correcao de vies estimada: [%.3f %.3f] m/s (esperado [%.3f %.3f] = -vies do DVL)\n', x(3), x(4), -corr);

figure('Name', 'Demo6 - EKF LBL+DVL');
subplot(1,2,1); hold on; grid on; axis equal;
plot(P(:,1), P(:,2), 'k-', 'LineWidth', 1.5);
plot(dr(:,1), dr(:,2), '-', 'LineWidth', 1.2);
plot(lbl(ok,1), lbl(ok,2), '.', 'MarkerSize', 8);
plot(ekf(:,1), ekf(:,2), '-', 'LineWidth', 1.5);
plot(B(:,1), B(:,2), 'k^', 'MarkerFaceColor', 'y', 'MarkerSize', 9);
legend('real', 'so DVL', 'LBL ponto a ponto', 'EKF LBL+DVL', 'transponders', 'Location', 'northeastoutside');
xlabel('x [m]'); ylabel('y [m]'); title('Trajetorias');
subplot(1,2,2); hold on; grid on;
t = (0:N-1)*dt;
plot(t, e_dr, 'LineWidth', 1.2); plot(t(ok), e_lbl, '.'); plot(t, e_ekf, 'LineWidth', 1.5);
set(gca, 'YScale', 'log'); xlabel('t [s]'); ylabel('Erro horizontal [m]');
legend('so DVL', 'LBL ponto a ponto', 'EKF'); title('Erro ao longo do tempo');
