function NSL = ruido_ambiente(f_kHz, estado_mar)
%RUIDO_AMBIENTE Nivel espectral do ruido ambiente [dB re 1 uPa^2/Hz].
%   Ajuste as curvas medias de Urick (forma de Knudsen, f^-5/3) usado por
%   Kurahashi & Gratta (arXiv:0712.1833): P(f,ns) = 94.5 - (50/3)*log10(f[Hz]) + 30*log10(ns+1)
%   baseado nas curvas de Urick (1-40 kHz); validado no mar ate ~25 kHz.
%   Nao inclui o ruido proprio do navio.
f = f_kHz * 1e3;
NSL = 94.5 - (50/3)*log10(f) + 30*log10(estado_mar + 1);
end
