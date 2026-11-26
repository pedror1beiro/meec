function [pest, Rm, x, y, n0, fs, pcoarse] = usbl_ping(p, SNRdB, mLong)
%USBL_PING Simula um ping USBL ao nivel do sinal e estima a posicao do alvo.
%   [pest, Rm, x, y, n0, fs, pcoarse] = usbl_ping(p, SNRdB, mLong)
%   p     : posicao real do transponder [x y z] em metros (z < 0)
%   SNRdB : SNR por amostra antes do filtro adaptado [dB]
%   mLong : (opcional) se > 0, acrescenta um par "longo" em x e em y com
%           espacamento d2 = mLong*lambda e resolve a ambiguidade de fase
%           usando o par curto (lambda/2). Por omissao 0 (so par curto).
%   pest  : posicao estimada (com o par longo, se existir)
%   pcoarse: posicao so com o par curto
%   Rm    : slant range medido;  x, y: sinais e saidas do filtro adaptado
if nargin < 3, mLong = 0; end
c   = 1500;  fs = 250e3;              % velocidade do som, amostragem
f0  = 20e3;  f1 = 30e3; Tp = 5e-3;    % chirp 20-30 kHz, 5 ms (BT = 50)
fc  = (f0+f1)/2; lambda = c/fc;       % lambda = 6 cm
d   = lambda/2;                       % par curto: 3 cm (sem ambiguidade)
E   = [0 0 0; d 0 0; 0 d 0];          % elementos 1..3 (L curto)
if mLong > 0
    d2 = mLong*lambda;                % par longo (ambiguo, mais preciso)
    E  = [E; d2 0 0; 0 d2 0];         % elementos 4 e 5
end
nE = size(E,1);

t  = (0:round(Tp*fs)-1)'/fs;
s  = cos(2*pi*(f0*t + (f1-f0)/(2*Tp)*t.^2)) .* (0.5 - 0.5*cos(2*pi*(0:numel(t)-1)'/(numel(t)-1)));
Nw = 2^nextpow2(round(1.0*fs));       % janela de rececao de ~1 s
f  = [0:Nw/2-1, -Nw/2:-1]'*fs/Nw;     % eixo de frequencias da FFT
S  = fft(s, Nw);
R0 = norm(p - E(1,:));                % percurso de ida (interrogacao)
sig_n = sqrt(mean(s.^2) / 10^(SNRdB/10));
x  = zeros(Nw, nE);
for k = 1:nE
    tau    = (R0 + norm(p - E(k,:)))/c;             % ida + volta ao elemento k
    x(:,k) = real(ifft(S .* exp(-1j*2*pi*f*tau))) + sig_n*randn(Nw,1);
end

% Filtro adaptado (matched filter) em forma analitica
Hpos = 2*(f > 0);
y = zeros(Nw, nE);
for k = 1:nE
    y(:,k) = ifft(fft(x(:,k)) .* conj(S) .* Hpos);
end
env = abs(y(:,1));
[~, n0] = max(env);
a = env(n0-1); b = env(n0); cc = env(n0+1);          % interpolacao parabolica
toa = (n0 - 1 + 0.5*(a-cc)/(a-2*b+cc)) / fs;
Rm  = c*toa/2;                                       % slant range

% Par curto -> cossenos diretores sem ambiguidade
dphx = angle(y(n0,2) * conj(y(n0,1)));
dphy = angle(y(n0,3) * conj(y(n0,1)));
ux = dphx*lambda/(2*pi*d);  uy = dphy*lambda/(2*pi*d);   % sin(theta) = dphi*lambda/(2*pi*d)
pcoarse = Rm*[ux uy -sqrt(max(0, 1 - ux^2 - uy^2))];
pest = pcoarse;

% Par longo -> resolver o inteiro k e refinar
if mLong > 0
    ph2x = angle(y(n0,4) * conj(y(n0,1)));
    ph2y = angle(y(n0,5) * conj(y(n0,1)));
    kx = round((2*pi*d2*ux/lambda - ph2x)/(2*pi));       % numero de ciclos em falta
    ky = round((2*pi*d2*uy/lambda - ph2y)/(2*pi));
    ux = (ph2x + 2*pi*kx)*lambda/(2*pi*d2);
    uy = (ph2y + 2*pi*ky)*lambda/(2*pi*d2);
    pest = Rm*[ux uy -sqrt(max(0, 1 - ux^2 - uy^2))];
end
end
