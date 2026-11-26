function [z, c, T, S] = carregar_argo(ficheiro)
%CARREGAR_ARGO Le um perfil Argo (pres, temp, psal) e calcula c(z) (Mackenzie).
%   [z, c, T, S] = carregar_argo('dados/argo_6901998_2025-07-20.csv')
%   z : profundidade [m] (aproximada pela pressao em dbar; diferenca < 1 %)
%   c : velocidade do som [m/s]
fid = fopen(ficheiro, 'r');
d = textscan(fid, '%f %f %f', 'Delimiter', ',', 'HeaderLines', 3);   % salta 3 linhas de cabecalho
fclose(fid);
z = d{1};  T = d{2};  S = d{3};
c = mackenzie(T, S, z);
% acrescenta superficie (z = 0) com o valor do primeiro nivel
z = [0; z];  c = [c(1); c];  T = [T(1); T];  S = [S(1); S];
end
