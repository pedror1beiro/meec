%% DEMO 5 - Orcamento do enlace acustico (equacao do sonar)
% Trabalho PERSE - Posicionamento acustico subaquatico
% Porque se usam 10-30 kHz e nao 100 kHz para alcances de quilometros?
%   SNR = SL - TL(r,f) - NL(f) + 10*log10(B*T),   TL = 20*log10(r) + alpha(f)*r/1000
% Comparar com as especificacoes: banda MF (20-34 kHz) ate ~7 km, banda LMF
% (14-19,5 kHz) para alem de 11 km (Sonardyne Ranger 2).
close all; clc;

SL  = 187;            % nivel de fonte [dB re 1 uPa @ 1 m]: transponder MF omni (Sonardyne)
SS  = 3;              % estado do mar
B   = 10e3; T = 5e-3; % largura de banda e duracao do chirp (parametros de projeto)
% ruido ambiente medido (ajuste de Urick/Knudsen, Kurahashi & Gratta, arXiv:0712.1833), por frequencia
G   = 10*log10(B*T);            % ganho do filtro adaptado = 17 dB
NL  = @(fk) ruido_ambiente(fk, SS) + 10*log10(B);   % ruido na banda [dB]
DT  = 10;                       % limiar de detecao [dB]

f = logspace(0, 2, 200);        % 1 a 100 kHz
figure('Name', 'Demo5 - Orcamento do enlace');
subplot(1,2,1);
loglog(f, thorp(f), 'LineWidth', 2); grid on;
xlabel('Frequencia [kHz]'); ylabel('\alpha [dB/km]');
title('Absorcao na agua do mar (Thorp)');

r = linspace(100, 20000, 800); fc = [15 25 50];
subplot(1,2,2); hold on; grid on;
for k = 1:numel(fc)
    TL  = 20*log10(r) + thorp(fc(k))*r/1000;
    snr = SL - TL - NL(fc(k)) + G;
    plot(r/1000, snr, 'LineWidth', 2, 'DisplayName', sprintf('%d kHz', fc(k)));
    rmax = r(find(snr >= DT, 1, 'last'));
    fprintf('%2d kHz: alpha = %5.2f dB/km, alcance (SNR >= %d dB) ~ %.1f km\n', fc(k), thorp(fc(k)), DT, rmax/1000);
end
plot([0 20], [DT DT], 'k--', 'DisplayName', 'limiar de detecao');
ylim([-40 60]); xlabel('Distancia [km]'); ylabel('SNR apos filtro adaptado [dB]');
title('SNR vs distancia (SL = 187 dB, estado do mar 3)'); legend('Location', 'northeast');

fprintf('\nSNR [dB] apos filtro adaptado:\n%8s %8s %8s %8s %8s\n', 'f [kHz]', '1 km', '3 km', '6 km', '10 km');
for k = 1:numel(fc)
    rr = [1000 3000 6000 10000];
    fprintf('%8d %8.0f %8.0f %8.0f %8.0f\n', fc(k), SL - (20*log10(rr) + thorp(fc(k))*rr/1000) - NL(fc(k)) + G);
end
