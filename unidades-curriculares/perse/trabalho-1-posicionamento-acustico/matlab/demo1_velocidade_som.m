%% DEMO 1 - Velocidade do som e o seu efeito na medida de distancia
% Trabalho PERSE - Posicionamento acustico subaquatico (USBL / SBL / LBL)
% Todos os sistemas medem TEMPOS de propagacao: r = c * t.
% Se a velocidade do som c assumida estiver errada, a distancia vem errada.
close all; clc;

% --- Perfil sintetico de temperatura (termoclina) -----------------------
z = (0:10:2000)';                       % profundidade [m]
T = 4 + 14*exp(-z/250);                 % 18 C a superficie -> ~4 C em profundidade
S = 35*ones(size(z));                   % salinidade [ppt]
c = mackenzie(T, S, z);                 % perfil de velocidade do som (SVP)

fprintf('c(0 m)    = %.1f m/s\n', c(1));
fprintf('c(1000 m) = %.1f m/s\n', c(z==1000));
fprintf('c(2000 m) = %.1f m/s\n', c(end));
[cmin, imin] = min(c);
fprintf('Minimo de c = %.1f m/s a %d m (canal SOFAR)\n', cmin, z(imin));

% --- Erro de distancia quando se assume c = 1500 m/s ---------------------
r  = linspace(0, 3000, 200);            % distancia real [m]
dc = [2 5 10 20];                       % erro na velocidade [m/s]

figure('Name', 'Demo1 - Velocidade do som');
subplot(1,2,1);
plot(c, z, 'LineWidth', 2); set(gca, 'YDir', 'reverse'); grid on;
xlabel('c [m/s]'); ylabel('Profundidade [m]');
title('Perfil de velocidade do som (Mackenzie 1981)');

subplot(1,2,2); hold on; grid on;
for k = 1:numel(dc)
    plot(r, r*dc(k)/1500, 'LineWidth', 2, 'DisplayName', sprintf('\\Deltac = %d m/s', dc(k)));
end
xlabel('Distancia (slant range) [m]'); ylabel('Erro de distancia [m]');
title('\Deltar = r \cdot \Deltac / c');
legend('Location', 'northwest');

fprintf('Ex.: r = 1000 m com erro de 10 m/s -> erro de %.1f m\n', 1000*10/1500);
