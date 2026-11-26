function c = mackenzie(T, S, D)
%MACKENZIE Velocidade do som na agua do mar (Mackenzie, 1981).
%   c = mackenzie(T, S, D)
%   T : temperatura [graus C]   (validade aprox. 2..30)
%   S : salinidade  [ppt]       (validade aprox. 25..40)
%   D : profundidade [m]        (validade aprox. 0..8000)
%   c : velocidade do som [m/s]
%   Ref: K. V. Mackenzie, "Nine-term equation for sound speed in the
%   oceans", J. Acoust. Soc. Am. 70(3), 807-812, 1981.
c = 1448.96 + 4.591*T - 5.304e-2*T.^2 + 2.374e-4*T.^3 ...
    + 1.340*(S-35) + 1.630e-2*D + 1.675e-7*D.^2 ...
    - 1.025e-2*T.*(S-35) - 7.139e-13*T.*D.^3;
end
