function R = modelo_posicionamento(P)
%MODELO_POSICIONAMENTO Erros de LBL, SBL e USBL para um cenario.
%   R = modelo_posicionamento(P) devolve, para cada sistema, o erro
%   aleatorio (covariancia 2x2, horizontal) e o erro sistematico (vies 2x1).
%   Campos de P (todos com valor por omissao em demo_interativa.m):
%     D         profundidade da agua [m]          alvo  posicao [x y] do alvo [m]
%     f         frequencia central [kHz]          SS    estado do mar (0-6)
%     SL        nivel de fonte [dB re 1uPa@1m]    B, T  banda [Hz] e duracao [s] do sinal
%     Llbl      lado da rede LBL [m]              Lsbl  baseline SBL [m]
%     d_usbl    abertura USBL [m]                 hdg   erro de heading [graus]
%     zv, cv    perfil real (verdade)             zc, cc  perfil usado pelo sistema
%
% Modelo:
%   aleatorio  : limite de Cramer-Rao do tempo de chegada com o SNR do
%                orcamento do enlace (Thorp + ruido de Urick/Knudsen)
%   sistematico: (1) velocidade do som usada vs perfil real (Argo)
%                (2) erro de heading do navio (SBL e USBL)
%   Nao inclui: refracao, multipercurso, erro do GNSS, erros de calibracao.

zt = P.D - 20;                                   % alvo 20 m acima do fundo
pt = [P.alvo(:)' -zt];
lam = 1500 / (P.f*1e3);
NL = ruido_ambiente(P.f, P.SS) + 10*log10(P.B);
G  = 10*log10(P.B*P.T);
beta = P.B / sqrt(12);

    function [sr, snr] = sigma_r(r)              % desvio padrao da distancia (TWTT)
        TL  = 20*log10(max(r,1)) + thorp(P.f)*r/1000;
        snr = P.SL - TL - NL + G;                % SNR apos filtro adaptado [dB]
        st  = 1 / (pi*sqrt(8)*beta*sqrt(10^(snr/10)));
        sr  = 1500*st/sqrt(2);
    end
    function db = vies_r(r, z1, z2)              % vies de distancia por c errada
        cv = c_media(P.zv, P.cv, z1, z2);  cu = c_media(P.zc, P.cc, z1, z2);
        db = r*(cu/cv - 1);
    end

% ---------- LBL: rede quadrada no fundo, centrada na origem ----------
h = P.Llbl/2;
B = [-h -h -P.D; h -h -P.D; h h -P.D; -h h -P.D];
[R.LBL, R.snr_lbl] = trilat_erro(B, pt, @sigma_r, @vies_r, 0);

% ---------- SBL: triangulo de hidrofones no navio (origem) ----------
L = P.Lsbl;
H = [-L/2 -L/(2*sqrt(3)) 0; L/2 -L/(2*sqrt(3)) 0; 0 L/sqrt(3) 0];
[R.SBL, R.snr_sbl] = trilat_erro(H, pt, @sigma_r, @vies_r, P.hdg);

% ---------- USBL: transceiver na origem ----------
r = norm(pt);  u = pt / r;
[sr, snr] = sigma_r(r);  R.snr_usbl = snr;
su = lam/(2*pi*P.d_usbl) * sqrt(2 / 10^(snr/10));      % por eixo (cosseno diretor)
J  = [u(1) r 0; u(2) 0 r];                               % d(x,y)/d(r,ux,uy)
Cu = J * diag([sr^2 su^2 su^2]) * J';
db = vies_r(r, 0, zt);
bias = db*u(1:2)';
a = P.hdg*pi/180;  Rz = [cos(a) -sin(a); sin(a) cos(a)];
bias = bias + (Rz*pt(1:2)' - pt(1:2)');
R.USBL = struct('C', Cu, 'b', bias, 'r', r);
R.r_usbl = r;

R.NL = NL;  R.G = G;
end

function [S, snr_min] = trilat_erro(Bref, pt, fsig, fvies, hdg)
% Erro de trilateracao 2D (profundidade conhecida) por linearizacao.
N = size(Bref,1);  J = zeros(N,2);  sr = zeros(N,1);  db = zeros(N,1);  snr = zeros(N,1);
for i = 1:N
    d = pt - Bref(i,:);  r = norm(d);
    J(i,:) = d(1:2) / r;
    [sr(i), snr(i)] = fsig(r);
    db(i) = fvies(r, -Bref(i,3), -pt(3));
end
W  = diag(1 ./ sr.^2);
C  = inv(J' * W * J);
b  = C * J' * W * db;
if hdg ~= 0                                   % referencia no navio: roda com o heading
    a = hdg*pi/180;  Rz = [cos(a) -sin(a); sin(a) cos(a)];
    b = b + (Rz*pt(1:2)' - pt(1:2)');
end
S = struct('C', C, 'b', b, 'r', 0);
snr_min = min(snr);
end
