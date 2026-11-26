function cm = c_media(z, c, z1, z2)
%C_MEDIA Velocidade media harmonica entre as profundidades z1 e z2 [m].
%   E a velocidade que converte corretamente tempo em distancia num
%   percurso reto entre essas profundidades (sem refracao).
a = min(abs([z1 z2])); b = max(abs([z1 z2]));
if b - a < 1
    cm = interp1(z, c, min(a, z(end)), 'linear', 'extrap'); return;
end
zz = linspace(a, b, 200);
zz = min(zz, z(end));                % abaixo do ultimo nivel: usa o ultimo valor
cc = interp1(z, c, zz);
cm = 1 / mean(1 ./ cc);
end
