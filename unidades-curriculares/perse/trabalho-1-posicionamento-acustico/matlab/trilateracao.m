function [p, H] = trilateracao(B, r, p0, z_fixo)
%TRILATERACAO Posicao por minimos quadrados nao lineares (Gauss-Newton).
%   Resolve  min_p  sum_i ( ||p - B(i,:)|| - r(i) )^2
%   B      : N x 3, posicoes conhecidas das referencias (transponders/hidrofones)
%   r      : N x 1, distancias medidas (slant ranges) [m]
%   p0     : 1 x 3, estimativa inicial
%   z_fixo : (opcional) profundidade conhecida pelo sensor de pressao.
%            Se for dado, so x e y sao estimados (problema 2D).
%   p      : 1 x 3, posicao estimada
%   H      : Jacobiano final (para calcular DOP)
if nargin < 4, z_fixo = []; end
p = p0(:)';
if ~isempty(z_fixo), p(3) = z_fixo; end
for it = 1:20
    d   = B - p;                          % vetores referencia - posicao
    rho = sqrt(sum(d.^2, 2));             % distancias previstas
    J   = -d ./ rho;                      % derivada de rho em ordem a p
    if ~isempty(z_fixo), J = J(:,1:2); end
    dp  = (J' * J) \ (J' * (r(:) - rho)); % passo de Gauss-Newton
    if isempty(z_fixo), p = p + dp'; else, p(1:2) = p(1:2) + dp'; end
    if norm(dp) < 1e-6, break; end
end
H = J;
end
